# MDQC Core (OSX)
# Version 0.1, 2013-10-28
# Copyright (c) 2013 AudioVisual Preservation Solutions
# All rights reserved.
# Released under the Apache license, v. 2.0

import subprocess
from collections import defaultdict
from os import path
import time
from re import compile, findall, UNICODE
import sys

# template (text file)
# generates a set of rules from a text file
# returns: list of (tag, comp, value) tuples
def template(tpl):
    rules = []
    with open(tpl, 'r') as t:
        s = t.readlines()
    for r in range(len(s)):
        q = s[r].split('\t')
        if q[1].strip() is not 'XX':
            rules.append((q[0].strip(), q[1].strip(), q[2].strip()))
    return rules

def exifMeta(file_path):

    meta = defaultdict(list)

    try:
        n = subprocess.Popen(['/usr/bin/exiftool'])
        fp = '/usr/bin/exiftool'
    except OSError:
        fp = '/usr/local/bin/exiftool'


    try:
        file_path = file_path.decode('utf-8')
    except:
        pass

    try:
        # executes exiftool against the media file with group output
        # exiftool is run twice: once for all but filesize,
        #				and one specifically for filesize
        # this is due to filesize requiring precise numerical output
        p = subprocess.Popen([fp, '-t', '-G', '--filesize', file_path], stdout=subprocess.PIPE)
        out = p.communicate()[0].splitlines()
        p.stdout.close()
        try:
            p.terminate()
        except:
            pass
        q = subprocess.Popen([fp, '-t', '-G', '-filesize#', file_path], stdout=subprocess.PIPE)
        out += q.communicate()[0].splitlines()
        q.stdout.close()
        try:
            q.terminate()
        except:
            pass
    except:
       return
       pass
    # formats the list into a dictionary
    for x in out:
        if 'ExifTool Version' in x or 'File Name' in x:
            continue
        y = x.split('\t')
        if y[2].strip():
            meta[y[1].strip()] = y[2].strip()
        else:
            meta[y[1].strip()] = ""
    return meta


# mnfoMeta (media file)
# generates metadata for the supplied media file
# returns: defaultdict of {tag: value} pairs
def mnfoMeta(file, useMediaInfoFile):

    meta = defaultdict(list)
    try:
        n = subprocess.Popen(['/usr/bin/mediainfo'])
        fp = '/usr/bin/mediainfo'
    except OSError:
        fp = '/usr/local/bin/mediainfo'

    if useMediaInfoFile == False:

        p = subprocess.Popen([fp, file],
                            stdout=subprocess.PIPE)
        out = p.communicate()[0].splitlines()
    else:
        try:
            import io
            f = io.open(file, mode="r", encoding="utf-8").read()
            out = f.splitlines()
        except:
            out = []

    # formats the list into a dictionary
    prefix = ""
    for x in out:
        try:
            if not ":" in x or 'File Name' in x:
                continue
            y = x.split(' :')
            if y[0].strip() == 'ID':
                prefix = "Track #" + str(y[1].strip()) + " "
            if y[1].strip():
                meta[prefix + y[0].strip()] = y[1].strip().decode('utf8')
            else:
                meta[prefix + y[0].strip()] = ""
        except Exception as e:
            print e
            pass

    return meta

# verify ( (tag, comparator, value), metadata dictionary )
# takes a rule tuple and returns if the metadata dictionary meets it
# for example: ( (X Resolution, 3, 400), metadata dictionary)
def verify(rule, dict):
    # unicode regex to split strings into lists
    word = compile("[\w\d'-\.\,]+", UNICODE)
    try:
        value = findall(word, dict[rule[0]])
    except:
        # if we're here, there was no value - check for non-existence
        if rule[1] == 2:
            return 2
        else:
            return 1
    # if it's a date, it should be reformatted into a date format
    if 'Date' in rule[0]:
        try:
            comp = time.mktime(time.strptime(rule[2].split(' ')[0],"%Y:%m:%d"))
            value = time.mktime(time.strptime(value.split(' ')[0],"%Y:%m:%d"))
        except:
            comp = findall(word, rule[2])
    else:
        # split the unicode string into a list of words/numbers
        comp = findall(word, rule[2])
    try:
        # value exists
        if rule[1] == 1:
            return 2
        # value does not exist
        if rule[1] == 2 and not value:
            return 2
        # value equals reference value
        if rule[1] == 3 and value == comp:
            return 2
        # value does not equal reference value
        if rule[1] == 4 and value != comp:
            return 2
        # value contains reference value
        if rule[1] == 5 and str(rule[2]).lower() in str(dict[rule[0]]).lower(): #any(k in s for s in value for k in rule[2]):
            return 2
        # value does not contain reference value
        if rule[1] == 6 and str(rule[2]).lower() not in str(dict[rule[0]]).lower(): #all(k in s for s in value for k in rule[2]):
            return 2
        # value is greater than
        if (rule[1] == 7 and
            tuple(float(f) for f in destring(value)) > tuple(float(f) for f in destring(comp))):
            return 2
        # value is at least
        if (rule[1] == 8 and
            tuple(float(f) for f in destring(value)) >= tuple(float(f) for f in destring(comp))):
            return 2
        # value is less than
        if (rule[1] == 9 and
            tuple(float(f) for f in destring(value)) < tuple(float(f) for f in destring(comp))):
            return 2
        # value is at most
        if (rule[1] == 10 and
            tuple(float(f) for f in destring(value)) <= tuple(float(f) for f in destring(comp))):
            return 2
        # nothing was true, so it must be false
        else:
            return 0
    except ValueError:
            # we get here if we tried an illegal operation
            # (e.g. unicode > unicode)
            # so we'll throw 'malformed operator'
            return 3

def lineno():
    import inspect
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

# validate (media asset, list of rule tuples)
# generates the metadata dictionary for the asset
# and compares each rule tuple against it
# in addition, it generates the output string for the asset, 
# providing a natural-language description of what happened
def validate(file, rules, type, useMediaInfoFile = False):
    verified_files = {}

    result, report = "", ""
    valid = True
    if type:
        meta = exifMeta(file)
    else:
        meta = mnfoMeta(file, useMediaInfoFile)
    for r in rules:
        if r[1] == 1:
            op = 'existent:'
        if r[1] == 2:
            op = "nonexistent:"
        if r[1] == 3:
            op = ''
        if r[1] == 4:
            op = "not"
        if r[1] == 5:
            op = "containing"
        if r[1] == 6:
            op = "not containing"
        if r[1] == 7:
            op = "greater than"
        if r[1] == 8:
            op = "at least"
        if r[1] == 9:
            op = "less than"
        if r[1] == 10:
            op = "at most"
        x = verify(r, meta)

        if x is 0:

            result += path.abspath(file) + ": FAILED at " + r[0] + " (" + meta[r[0]] + " is not " + op + " " + r[2].rstrip() + ")\n"

            # <File Path> FAILED <tag> not <operation> <value>  <tag1> not <operation1> <value1> ....
            if file in verified_files:
                verified_files[file] = str(verified_files[file]) + "\t" + str(r[0]) + " not " + op + " " + r[2].strip() + "\t"
            else:
                verified_files[file] = path.abspath(file) + "\tFAILED\t" + str(r[0]) + " not " + op + " " + r[2].strip() + "\t"

            valid = False
        elif x is 1:


            result += path.abspath(file) + ": FAILED at " + r[0] + " (tag not found)\n"

            # <File Path> FAILED tag not found <tag>    tag not found <tag1>  ....
            if file in verified_files:
                verified_files[file] = str(verified_files[file]) + "\t" + " tag not found " + str(r[0]) + "\t"
            else:
                verified_files[file] = path.abspath(file) + "\tFAILED\t" + " tag not found " + str(r[0]) + "\t"

            valid = False
        elif x is 3:


            result += path.abspath(file) + \
                ": Malformed comparison operator (" + \
                op + " does not operate on " + meta[r[0]] + \
                " and " + r[2] + ")\n"

            # <File Path> FAILED <operator> does not operate on <tag>   <operator1> does not operate on <tag1> ...
            if file in verified_files:
                verified_files[file] = str(verified_files[file]) + "\t"+ str(op) + " does not operate on " + r[0] + "\t"
            else:
                verified_files[file] = path.abspath(file) + "\tFAILED\t" + str(op) + " does not operate on " + r[0] + "\t"

            valid = False

    for single_verified_files in verified_files:
        report += verified_files[single_verified_files] + "\n"

    if valid:
        return path.abspath(file) + ": PASSED", path.abspath(file) + "\tPASSED\n"

    return result.rstrip(), report

def destring(t):
    l = []
    for x in t:
        try:
            l.append(float(x))
        except:
            continue
    if len(l) == 0:
        l.append('bad string')
    return l

