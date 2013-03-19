import re
import subprocess
import sys
import os
import time

imgs = []

# this is split into two fake "relational tables"
# fie[] and val[] are the metadata to be validated as Field:Value
# fld[], rld[], and vld[] are Field Index:Rule:Reference
# Thus, they can be operated upon separately while retaining x-refs
fie = []
val = []

fld = [] # int index of fie[]
rld = [] # rule operator
vld = [] # validitity check

# ingests each three-part rule ([VAL] [OPERATOR] [REFERENCE])
def setRule(field, op, v):
	i = fie.index(field)
	fld.append(i)
	rld.append(op)
	vld.append(v)
	return

def writeRules(fn):
	f = open(fn, 'w')
	for x in range(len(fld)):
		f.write(fld[x], rld[x], vld[x])
	return

# ingest template into arrays
# invokes setRule to link between "tables"
def template(tpl):
	with open(tpl, 'r') as t:
		s = t.readlines()
	for r in range(len(s)):
		q = s[r].split('\t')
		setRule(q[0].strip(), q[1].strip(), q[2].strip())
	return
	
# string regex check (alphanumeric, numeric)
def chkAN(s, ch):
	if ch == 'd':
		reg = re.compile('\D')
	elif ch == 'w':
		reg = re.compile('\W')
	else:
		return "Invalid regex"
	return reg.match(s) == None

# validation function
def validate(i):
	testwith = val[fld[i]]

	# value exists
	if rld[i] == 'EX':
		return testwith
	# value does not exist
	if rld[i] == 'NX':
		return not testwith
	# value equals reference value
	if rld[i] == 'EQ':
		return testwith == vld[i]
	# value does not equal reference value
	if rld[i] == 'NQ':
		return testwith != vld[i]
	# value contains reference value
	if rld[i] == 'CT':
		return vld[i] in testwith
	# value does not contain reference value
	if rld[i] == 'NT':
		return vld[i] not in testwith
	# value is greater than (int)
	if rld[i] == 'GT':
		return int(testwith) > int(vld[i])
	# value is less than (int)
	if rld[i] == 'LT':
		return int(testwith) < int(vld[i])
	# value is of type (alpha, numeric, both)
	if rld[i] == 'TY':
		return chkAN(testwith, vld[i])
	# value is of length less than (int)
	if rld[i] == 'LL':
		return len(testwith) < vld[i]
	# value is of length greater than (int)
	if rld[i] == 'GL':
		return len(testwith) > vld[i]
	# skip null checks
	if rld[i] == '' or rld[i] == 'XX':
		return True
	# general check for bad operators
	else:
		return "No such operator:", rld[i]

# clear all arrays
def clear():
	del fie[:]
	del val[:]
	del rld[:]
	del vld[:]
	del fld[:]
	return

def readMeta(f):
	tmp = subprocess.check_output(["exiftool", f]).splitlines()
	for x in range(len(tmp)):
		fie.append(tmp[x].split(':', 1)[0].strip())
		val.append(tmp[x].split(':', 1)[1].strip())
	# eventually, this is going to support other metadata tools
	# I just need to get them running on this machine
	return

def help():
	print "Invalid input"
	print "Usage: qctool -g [reference file]"
	print "       (Generates rules file)"
	print ""
	print "       qctool -v [directory] [rules]"
	print "       (Validates files against rules)"
	return
### MAIN ###

if __name__ == "__main__":

	p1 = []
	d = time.strftime("%Y%m%d%H%M%S")

	if len(sys.argv) < 2:
		help()
		sys.exit()
	elif sys.argv[1] == "-g":
		fn = "rules_" + d + ".txt"
		f = open(fn, 'w+')
		readMeta(sys.argv[2])
		for n in range(len(fie)):
			str = fie[n] + "\tXX\t" + val[n] + "\n"
			f.write(str)

	elif sys.argv[1] == "-v":
		for root, subFolders, files in os.walk(sys.argv[2]):
			for file in files:
				p1.append(os.path.join(root, file))

		for a in range(len(p1)):
			if ".tif" in p1[a] or if ".jp" in p1[a]:
				imgs.append(p1[a])
		for n in range(len(imgs)):
			result = str(imgs[n]) + ":"
			readMeta(imgs[n])
			template(sys.argv[3])
			good = True
			logfile = "log_" + d + ".txt"
			for y in range(len(rld)):
				if not validate(y):
					result += "\nFAILED on field " + fie[fld[y]] + " test: " + val[fld[y]] + " " + rld[y] + " " + vld[y]
					good = False
			if good:
				result += " PASSED"
			print result
			open(logfile, "a+b").write(result)
			clear()
	else:
		help()
		sys.exit()