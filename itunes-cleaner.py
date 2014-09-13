#!/usr/bin/python

# a work in progress... very.

import sys
import re
import os

debug=False
dbfile=os.path.join(os.path.expanduser('~'),'Music/iTunes/iTunes Music Library.xml')

try:
  fp=open(dbfile,'r')
except Exception, e:
  print "Unable to open library db: %s" % e
  sys.exit(1)

def is_dict_open(s):
  # <dict> and </dict> tags appear always to occure on their
  # own line (which is rather helpful)
  m=re.search('\<dict\>',s)
  return m is not None

def is_dict_close(s):
  m=re.search('\<\/dict\>',s)
  return m is not None

def parse_kv_pair(s):
  m=re.search('\<key\>(.+)\<\/key\>\<(.+)\>(.+)\<\/.+\>',s)
  if m is None: return None,None

  if m.group(2)=='integer':
    return m.group(1),int(m.group(3))
  else:
    return m.group(1),m.group(3)

library = {} # global / library config settings

tracks_by_id = {} 
files_to_id = {}
tags_to_id = {}

thistrack = {}
flagged = set()

# states:
# - 0_OPEN
# - 1_IN_DB
# - 2_IN_TRACKS
# - 3_TRACK_DEETS

print "Parsing your DB..."
state='0_OPEN'
for line in fp.readlines(): #TODO: check if this is iterable or nabs full list
  if '0_OPEN'==state: # looking for first <dict>
    if is_dict_open(line): state='1_IN_DB'
  elif '1_IN_DB'==state:
    if is_dict_open(line): 
      state='2_IN_TRACKS'
      continue
    
    (k,v)=parse_kv_pair(line)
    if k is not None:
      library[k]=v
  elif '2_IN_TRACKS'==state:
    # we ignore the primary key defs since the ID is redefined inside the track dict
    if is_dict_open(line): state='3_TRACK_ID'
    elif is_dict_close(line):
      break
  elif '3_TRACK_ID'==state:
    if is_dict_close(line):
      state='2_IN_TRACKS'

      if not thistrack.has_key('Album'):
        thistrack['Album']='Unknown'

      if not thistrack.has_key('Artist'):
        thistrack['Artist']='Unknown'

      try:
        tid=thistrack['Track ID']
        tracks_by_id[tid]=thistrack

        if files_to_id.has_key(thistrack['Location']):
          files_to_id[thistrack['Location']].append(tid)
          flagged.add(tid)
        else:
          files_to_id[thistrack['Location']]=[tid]

        tagstr=thistrack['Artist']+thistrack['Album']+thistrack['Name']
        thistrack['tagstr']=tagstr # tie this on since we use it if flagged

        if tags_to_id.has_key(tagstr):
          tags_to_id[tagstr].append(tid)
          flagged.add(tid)
        else:
          tags_to_id[tagstr]=[tid]

        thistrack={}
        continue
      except Exception, e:
        print "[!] oddness happened on track %d: %s" % (tid,e)
        continue

    (k,v)=parse_kv_pair(line)
    if k is not None:
      thistrack[k]=v
     
print "Cool, found %d tracks, of which %d are flagged as dupe." % (len(tracks_by_id),len(flagged))

fcount=1
for tid in flagged:
  print "--- Dupe %d: %d tracks." % (fcount,len(tags_to_id[tracks_by_id[tid]['tagstr']]))
  fcount+=1

  c=1
  for fid in tags_to_id[tracks_by_id[tid]['tagstr']]:
    displocation=tracks_by_id[fid]['Location'].replace('%20',' ')
    m=re.search('file://localhost/Users/[a-zA-Z0-9]+/Music/iTunes/iTunes Media/Music/(.+)$',
      displocation) 
    if m is not None:
      displocation=m.group(1)    

    print "[%d]\t%s - %s - %s\n\t%s" % (fid,tracks_by_id[fid]['Artist'],tracks_by_id[fid]['Album'],
      tracks_by_id[fid]['Name'],displocation)
    c+=1
 
