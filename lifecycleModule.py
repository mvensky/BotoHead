#!/usr/bin/env python
import argparse
import sys
from os import environ
import os
import boto3
from subprocess import call
import json

def folderFinder(aBucket):
    # get the 2-level folders

    file = open("bucketObjects", "r")
    sortedLevels = []
    justFolders = []
    for line in file:
        levelList = line.split()
        if levelList[1].find('/') > -1:
            #print levelList[1]
            justFolders = levelList[1].split('/')
            #print justFolders
            sortedLevels.append(justFolders[0] + '/')
            justFolders = []

    sortedLevels = list(set(sortedLevels) )
    #print sortedLevels
    return(sortedLevels)

# to get around tzinfo in datatime.datetime type
def notSerial(time):
    #print '************** heres the time ***********'
    #print time
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Los_Angeles')
    #zuluGone = datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S.%f+00:00')
    #zuluGone = datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S.%d+00:00')
    #zuluGone = datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S+00:00')
    zuluGone = datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S+00:00')
    zuluGone = zuluGone.replace(tzinfo=from_zone)
    la_datetime = str(zuluGone.astimezone(to_zone) )
    return la_datetime

def buildTransitionOnly(policy, transformDays,bucketName,index, prefix):
    policy['Rules'].append(
         {
             'ID': bucketName + 'Rule' + str(index),
             'Prefix': prefix,
             'Status': 'Enabled',
             'Transitions': [
                 {
                     'Days': transformDays,
                     'StorageClass': 'GLACIER'
                 },
             ],
#            'NoncurrentVersionTransitions': [
#                {
#                    'NoncurrentDays': transformDays,
#                    'StorageClass': 'GLACIER'
#                },
#            ],
#            'AbortIncompleteMultipartUpload': {
#                'DaysAfterInitiation': 7
#            }
         }
    )

    return(policy)

def buildExpirationOnly(policy, expireDays,bucketName,index, prefix):
    policy['Rules'].append(
         {
             'Expiration': {
                 'Days': expireDays,
             },
             'ID': bucketName + 'Rule' + str(index),
             'Prefix': prefix,
             'Status': 'Enabled',
#            'NoncurrentVersionExpiration': {
#                'NoncurrentDays': expireDays
#            },
#            'AbortIncompleteMultipartUpload': {
#                'DaysAfterInitiation': 7
#            }
         }
    )

    return(policy)


def buildTransAndExpire(policy, transformDays,expireDays,bucketName,index, prefix):
    policy['Rules'].append(
         {
             'Expiration': {
                 'Days': expireDays,
             },
             'ID': bucketName + 'Rule' + str(index),
             'Prefix': prefix,
             'Status': 'Enabled',
             'Transitions': [
                 {
                     'Days': transformDays,
                     'StorageClass': 'GLACIER'
                 },
             ],
#            'NoncurrentVersionTransitions': [
#                {
#                    'NoncurrentDays': transformDays,
#                    'StorageClass': 'GLACIER'
#                },
#            ],
#            'NoncurrentVersionExpiration': {
#                'NoncurrentDays': int(transformDays)*2
#            },
#            'AbortIncompleteMultipartUpload': {
#                'DaysAfterInitiation': 7
#            }
         }
    )

    return(policy)

def buildLifecyclePolicy(theBucket,sortedLevels, transitionAnswer, daysToTransition, expirationAnswer, daysToExpiration):
    lifecyclePolicy = {'Rules' : [] }
    index = 1

    if transitionAnswer == 'Y' and expirationAnswer == 'Y':
        if len(sortedLevels) == 0:
            newLifecyclePolicy = buildTransAndExpire(lifecyclePolicy,int(daysToTransition),int(daysToExpiration),theBucket,index, '')
        else:
            for prefix in sortedLevels:
                newLifecyclePolicy = buildTransAndExpire(lifecyclePolicy,int(daysToTransition),int(daysToExpiration),theBucket,index, prefix)
                index = index + 1
    if transitionAnswer == 'Y' and expirationAnswer == 'N':
        if len(sortedLevels) == 0:
            newLifecyclePolicy = buildTransitionOnly(lifecyclePolicy, int(daysToTransition),theBucket,index, '')
        else:
            for prefix in sortedLevels:
                newLifecyclePolicy = buildTransitionOnly(lifecyclePolicy, int(daysToTransition),theBucket,index, prefix)
                index = index + 1
    if transitionAnswer == 'N' and expirationAnswer == 'Y':
        if len(sortedLevels) == 0:
            newLifecyclePolicy = buildExpirationOnly(lifecyclePolicy, int(daysToExpiration),theBucket,index, '')
        else:
            for prefix in sortedLevels:
                newLifecyclePolicy = buildExpirationOnly(lifecyclePolicy, int(daysToExpiration),theBucket,index, prefix)
                index = index + 1
    if transitionAnswer == 'N' and expirationAnswer == 'N':
        print "You have elected not to expire and not to transition"
        print "There is nothing for this program to do"
        exit(1)
    return(newLifecyclePolicy)


def main(callBucket, levelParam, glacierDays, expireDays, forceParam):
    # get all arguments lined up
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', '-b', help="name of S3 bucket", type= str)
    parser.add_argument('--level', '-l', help="first level folder or prefix name (one/two)", type= str)
    parser.add_argument('--glacier', '-g', help="number of days before transition to glacier", type= int)
    parser.add_argument('--expire', '-e', help="number of days before expiration of affected object(s)", type= int)
    parser.add_argument('--force', '-f', help="if there is a pre-existing policy: force overwrite (True/False)", type= str)
    parser.add_argument('--testRun', '-t', help="can be run without committing policies to view output only (True/False)", type= str)
    args =  parser.parse_args()


    # this logic is solely for catching calls to main from testing software
    if callBucket != " ":
        args.bucket = callBucket
        args.level = levelParam
        args.glacier = glacierDays
        args.expire = expireDays
        args.force = forceParam
        #print args

    # return values for assert testing
    returnedDict = {
        'bucketName'		: None,
        'tooMany'		: None,
        'hasLifecycle'		: None,
        'versioned'		: None,
        'glacierAndExpire'	: None, 
        'glacierOnly'		: None,
        'expireOnly'		: None,
        'forceOverwrite'	: None,
        'nothing'		: None,
    }

    # you have to specify something
    if len(sys.argv) == 1 and callBucket == " ":
        parser.print_help()
        sys.exit(1)
    
    # too dangerous to sweep through all buckets and specify an expiration
    if args.bucket == None and args.expire != None:
        print "Error: No expiration/deletion will occur without a bucket name"
        print "In order to specify an expiration parameter you must specify a bucket name"
        exit(2)
    
    if os.getenv("AWS_PROFILE") is None:
        print "Error: Please set AWS_PROFILE to a value corresponding to the AWS account you wish to access"
        exit(3)
    
    # the force flag is intended to force an overwrite of existing bucket lifecycle policies with what we have here
    # python booleans take any non-null value to be true; not just t/f
    if args.force is not None and args.force not in ("True", "False"):
        print "Error: Valid values for force are True or False"
        exit(4)
    
    # must keep things in glacier at least 90 days to avoid excessive charges
    if args.glacier is not None and args.expire is not None and (abs(args.glacier - args.expire) < 90) and args.force :
            print "Error: You should store objects in glacier for at least 90 days in order to avoid excessive charges"
            print "The difference between when items are placed in glacier and when items are expired should be > 90 days"
            exit(5)
    
    # level is a required parameter
    if args.level is None or args.level not in ("one", "two"):
        print 'Error: Valid values for level are "one" or "two"'
        print 'Level is a required parameter: You must specify a level of either "one" or "two"'
        exit(6)
    
    # user must specify for something to do
    if args.glacier == None and args.expire == None:
        print "Error have not specified either an expiration interval or a glacier-migration interval"
        print "Please specify expiration and/or glacier and try again"
        exit(7)
    
    
    # if no bucket is specified do all the buckets; exception occurs above; can't do all buckets and expire
    # otherwise do only the named bucket
    s3 = boto3.client('s3')
    buckets =  s3.list_buckets()
    allBuckets = buckets['Buckets']
    bucketList = []
    if args.bucket != None:
        bucketList.append(args.bucket)
    else:
        for bucket in allBuckets:
            bucketList.append(bucket['Name'])
    
    #build out the file of all objects for all buckets
    if os.path.isfile("bucketObjects"):
        status = call(["rm", "bucketObjects"])

    # check if bucket is a valid name
    checkBucketList = []
    for checkBucket in allBuckets:
        checkBucketList.append(checkBucket['Name'])
    if args.bucket in checkBucketList or callBucket in checkBucketList or args.bucket == None:
        pass
    else:
        print "Error: ", args.bucket, " not found in ", os.getenv("AWS_PROFILE")
        print "If this corresponds to the correct account check your spelling"
        exit(8)
    
    for bucket in bucketList:
        print "**************** ", bucket, " ****************"
        returnedDict['bucketName'] = bucket
        status = call(["./pythonHelper-v2.bsh", bucket ])
    
        if args.level == 'two':
            sortedList = folderFinder(bucket)
        else:
            sortedList = []
    
        # if the number of level-2 objects; ie. folders exceeds 100; error out and suggest either bucket level management
        # or reduction in the number of "level-2" objects
        tooMany = False
        if len(sortedList) >= 100: 
            print "Warning: ", bucket, " has ", len(sortedList) , " folders: 100 is the maximum AWS number of policies allowed per bucket"
            print 'Either use level "one" for bucket layer management or reduce the number of level "two" objects'
            print "No lifecycle policies will be applied to ", bucket
            tooMany = True
    
        # remember to check for existing lifecyle policy and skip if force=False
        try:
            response =  s3.get_bucket_lifecycle_configuration(Bucket=bucket)
            hasLifecycle = True
        except:
            hasLifecycle = False
        returnedDict['hasLifecycle'] = hasLifecycle

            
        if hasLifecycle:
            print bucket , " has a lifecycle policy"
    
        # if there is no versioning don't allow expiration
        versionResponse = s3.get_bucket_versioning(Bucket=bucket)
        versionEnabled = False
        if 'Status' in versionResponse:
            if versionResponse['Status'] == "Enabled":
                print "For bucket ", bucket, " versioning is enabled"
                versionEnabled = True
                #print json.dumps(versionResponse, indent=4)
    
        returnedDict['versioned'] = versionEnabled

        if os.path.isfile("bucketObjects"):
            status = call(["rm", "bucketObjects"])
    
        # tooMany is a policy breaker: bail out of loop can't apply a policy to this many folders
        returnedDict['tooMany'] = tooMany
        if tooMany == True:
            continue
    
        if args.force == None or args.force == 'False':
            force = False
        elif args.force == 'True':
            force = True
    
        #print "Force lifecycle overwrite = ", force
        #print "Force args lifecycle overwrite = ", args.force
        #print type(force)
        #print type(args.force)
        newLifecyclePolicy = {}
    
        if (hasLifecycle and versionEnabled and force) or (not(hasLifecycle) and versionEnabled and force) or\
            (not(hasLifecycle) and versionEnabled and not(force) ):
            #print "fire policy unrestricted"
            if args.glacier != None and args.expire != None:
                newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'Y', args.glacier, 'Y', args.expire)
                returnedDict['glacierAndExpire'] = True
            elif args.glacier == None and args.expire != None:
                newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'N', args.glacier, 'Y', args.expire)
                returnedDict['expireOnly'] = True
            elif args.glacier != None and args.expire == None:
                newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'Y', args.glacier, 'N', args.expire)
                returnedDict['glacierOnly'] = True
    
            returnedDict['forceOverwrite'] = force
            if args.testRun != 'True':
                s3.put_bucket_lifecycle_configuration(Bucket=bucket,LifecycleConfiguration=newLifecyclePolicy)
    
        if (not(hasLifecycle) and not(versionEnabled) and not(force) ) or (not(hasLifecycle) and not(versionEnabled) and force ) or\
           (hasLifecycle and not(versionEnabled) and force ):
            #print "fire policy NO delete"
            # will not fire expiration 365 used as a safe "default value"
            # the 365 is a dummy place holder
            #newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'Y', args.glacier, 'N', 365)
            if args.glacier != None and args.expire != None:
                #newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'Y', args.glacier, 'Y', args.expire)
                returnedDict['glacierAndExpire'] = False
                returnedDict['nothing'] = True
            elif args.glacier == None and args.expire != None:
                #newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'N', args.glacier, 'Y', args.expire)
                returnedDict['expireOnly'] = False
                returnedDict['nothing'] = True
            elif args.glacier != None and args.expire == None:
                newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'Y', args.glacier, 'N', 365)
                returnedDict['glacierOnly'] = True
            elif args.glacier == None and args.expire == None:
                newLifecyclePolicy = buildLifecyclePolicy(bucket, sortedList , 'N', args.glacier, 'N', args.expire)
                returnedDict['nothing'] = True


            returnedDict['glacierOnly'] = True
            returnedDict['forceOverwrite'] = force

            if newLifecyclePolicy != {}:
                if args.testRun != 'True':
                    s3.put_bucket_lifecycle_configuration(Bucket=bucket,LifecycleConfiguration=newLifecyclePolicy)
   
    
        if newLifecyclePolicy != {}:
            print ""
            if args.testRun != 'True':
                print "********* Here's the new lifecycle that was applied *********"
            elif args.testRun == 'True':
                print "********* THIS WAS ONLY A TEST RUN; NO POLICIES WERE APPLIED AT THIS TIME  *********"
            print json.dumps(newLifecyclePolicy, indent=4)
        else:
            print ""
            print "No lifecycle policy was applied: make sure bucket, level, forceOverwrite, expire and glacier are set correctly."
            print "Remember you can not set expiration for a bucket without versioning: also expiration must be set for individual buckets"
        
    return(returnedDict)

if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1][0:1] == "-":
        main(" ", " ", " ", " ", " ")
        
#pauseMe = raw_input("Stop here")

# non-current will not be considered for this version

