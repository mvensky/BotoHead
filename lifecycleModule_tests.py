#!/usr/bin/env python
# this is an example of a test against extant lifecycle policy as just applied
# assert_equal(sorted(response['Rules']),  sorted(s3.get_bucket_lifecycle_configuration(Bucket='mvensky-second')['Rules']) )
from nose.tools import *
import lifecycleModule
import boto3
def test_driver():
    s3 = boto3.client('s3')
    # case 1
    reply = lifecycleModule.main('mvenskybucketoregon', "one", 30, 365, "True")
    try:
        assert reply['glacierAndExpire']
        print "Expire and glacier passed"
        print "Case 1"
        print reply
    except:
        pass

    # case 2
    reply = lifecycleModule.main('mvenskybucketoregon', "one", 30, 365, "False")
    try:
        assert reply['glacierAndExpire']
        print "Expire and glacier passed"
        print "Case 2"
        print reply
    except:
        print "Expect to fail"

    #case 3
    reply = lifecycleModule.main('mvensky-second', "one", 30, None, "False")
    try:
        assert reply['glacierOnly']
        print "Glacier only passed"
        print "Case 3"
        print reply
    except:
        print "Expect to fail"

    #case 4
    response = s3.delete_bucket_lifecycle(Bucket='mvensky-single-level')
    reply = lifecycleModule.main('mvensky-single-level', "one", 30, None, "False")
    try:
        assert reply['glacierOnly']
        print "Glacier only passed"
        print "Case 4"
        print reply
    except:
        pass

    #case 5
    response = s3.delete_bucket_lifecycle(Bucket='mvensky-single-level')
    reply = lifecycleModule.main('mvensky-single-level', "one", 30, None, "True")
    try:
        assert reply['glacierOnly']
        print "Glacier only passed"
        print "Case 5"
        print reply
    except:
         pass

    #case 6 
    response = s3.delete_bucket_lifecycle(Bucket='mvenskybucketoregon')
    reply = lifecycleModule.main('mvenskybucketoregon', "one", 30, 365, "True")
    try:
        assert reply['glacierAndExpire']
        print "Expire and glacier passed"
        print "Case 6"
        print reply
    except:
        print reply

    # case 7
    reply = lifecycleModule.main('mvensky-second', "one", 30, None, "True")
    try:
        assert reply['glacierOnly']
        print "Glacier only passed"
        print "Case 7"
        print reply
    except:
        pass

    # case 8
    response = s3.delete_bucket_lifecycle(Bucket='mvenskybucketoregon')
    reply = lifecycleModule.main('mvenskybucketoregon', "one", 30, 365, "False")
    try:
        assert reply['glacierAndExpire']
        print "Expire and glacier passed"
        print "Case 8"
        print reply
    except:
         pass

    # case 9
    # check for tooMany
    reply = lifecycleModule.main('mvensky-many-folders', "two", 30, 365, "False")
    try:
        assert reply['glacierAndExpire']
        print "Expire and glacier passed"
        print "Case 9"
        print reply
    except:
        print "Case 9"
        print reply

test_driver()
