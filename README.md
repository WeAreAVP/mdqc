mdqc
====

Tool to validate metadata against a user-generated set of rules.  Dependent on exiftool in $PATH

Currently supports exiftool; in the future, will support more metadata input.  See JIRA for more information.

Invocation:

python qctool.py -g file
(generates rules template based on metadata from file)

python qctool.pv -v directory rules
(validates all valid files under directory against rules)

Rules:

general form: FIELD OP VALUE

Valid OP codes:

EX - exists
NX - does not exist
GT - greater than
LT - less than
EQ - equal to
NQ - not equal to
CT - contains
NT - does not contain
TY - type (alphanumeric (w), numeric (d))
LL - length less than
GL - length greater than
