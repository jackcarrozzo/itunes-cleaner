#!/usr/bin/python

# a work in progress.

import sys
import re

debug=True
filename='/Users/jackc/Music/iTunes/iTunes Music Library.xml'

try:
  fp=open(filename,'r')
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
     
print "Cool, found %d tracks, of which %d are flagged." % (len(tracks_by_id),len(flagged))

for tid in flagged:
  print "---------"

  c=1
  for fid in tags_to_id[tracks_by_id[tid]['tagstr']]:
    print "%d:\t[%d]\t%s - %s - %s\n\t%s" % (c,fid,tracks_by_id[fid]['Artist'],tracks_by_id[fid]['Album'],
      tracks_by_id[fid]['Name'],tracks_by_id[tid]['Location'])
    c+=1
 
