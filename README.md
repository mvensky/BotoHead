#### S3 lifecycle Requirements and Feature Set - Version 6

* A requirement is to be able to mention either a single bucket, or if no single bucket is mentioned to do all buckets in the AWS_PROFILE’s account.

* If no bucket is mentioned do not set expiration for deletion across all buckets. In other words you must specify a bucket on an individual basis in order to set a lifecycle policy with deletion. The program will exit with an Error, explanation and code 2 if expiration is mentioned without a bucket name.

* If you just type in the program name, lifecycleModule.py, without any arguments you will be presented with a help screen from argparse. The program will exit with code 1.

* The program requires AWS CLI access, meaning an AWS_PROFILE value must be set for a user id with proper access to s3 in the account of interest. If no AWS_PROFILE is set the program will exit with an Error, explanation and code 3.

* There is a force-flag which permits the overwriting of extant lifecycle policies. Valid values are True or False. Other values will cause the program to end with an Error, explanation and code 4. The program defaults to False if no value is given.

* Amazon states that they expect items to be kept in glacier for a period of at least 90 days if financial penalties are not to be imposed. If the difference between the glacier start days and the time to expire do not differ by at least 90 days the program will exit with an Error, explanation and code 5.

* As a note, you can specify a policy for days to glacier migration for any bucket or set without regard to versioning status. In order to specify expiration or glacier and expiration, versioning must be set on the bucket.

* The program operates at two levels in the bucket/folder realm. DevOps consensus is that level-one is the bucket itself, level-two is the first folder(s) within the bucket. Level is a required parameter and valid values are “one” or “two”.

* Some considerations are that by this definition a bucket of only objects without any folders basically has no level-two. The objects themselves are not considered a level, only buckets or folders contained within are levels. If you specify level two the program will identify all level-two folders and create a separate rule for each one of them. AWS limits the number of rules to 100 per bucket. If there is a bucket  with more than 100 level-2 folders the program will print a warning and not apply any policies.

* If level-two is specified and during the sweep of buckets in an account a bucket is encountered with no folders, the program will apply the policy to the bucket itself.

* The program expects glacier and/or expiration to be specified. If  neither is specified the program will end with an Error, explanation and code 7.

* Assuming a properly configured AWS_PROFILE with s3 access, the program can discover what buckets are out there. If you elect to specify a bucket name that doesn’t exist, either by misspelling or mistake, the program will end with an Error, explanation and code 8.

* The program checks the lifecycle policy status of each bucket before applying the new policy. If a bucket is encountered that already has a policy and you did not specify force then the bucket is skipped over and the new policy is not applied. You will receive an explanation on how to correct the situation.

* Those buckets with extant lifecycle policies will be flagged in the output. Also those buckets with versioning enabled will also be flagged in the program’s output.

* Finally the program outputs the policy and implemented for each bucket or an explanation why no policy was applied.

* At this time there was a requirement to only handle glacier and expiration. There is no coverage for non-current/previous versions. This can easily be added.

* The is also a testRun-flag, you can run the command with whatever other parameters you intend, see what would be done and if that meets your needs, rerun the program without testRun flag  and have those changes be applied. The default is false for testRun.

* The program is implemented in Python using boto3. In order get a listing of all level-two objects the programs calls ‘aws s3api list-objects’ and spools the output out to a temporary file in order to overcome boto’s list_object 1000 result limitation.

* The caveat is as follows: in order to find the level-two folders all objects metadata are spooled into a file, for those buckets with millions of objects this process can take some time. We may want to consider a database, refreshed periodically to give us a listing of all objects on a bucket-by-bucket basis.

* In the meantime, you might consider setting an expiration policy that gets rid of the older-ancient objects that no longer need be kept, then rerunning the program to set all the level-two folders to your satisfaction.

* This is version 6 of the lifecycleModule. For this version we have added the ability to specify specific folders within a single bucket or all buckets. Note, there is no need for the folder to exist in order for you to apply the rule. You must however place a '/' at the end of the folder name otherwise the program will exit an Error, explanation and code 9.

#### Testing

The program uses argparse to provide it’s interface, unfortunately this means that the nose test harness will not work. Hence the program has been refactored into a module that can be driven by a test program.

The requirements for handling tooMany, hasLifecycle, hasVersion and force were used to generate a matrix; the fifth column being the intended outcome and the other four columns are input.

TooMany | hasLifecycle | Versioning | ForceOverwrite | Fire Rule       |
--------|--------------|------------|----------------|-----------------|
TRUE | TRUE | TRUE | TRUE | FALSE
TRUE | TRUE | TRUE | FALSE | FALSE
TRUE | TRUE | FALSE | FALSE | FALSE
TRUE | FALSE | FALSE | FALSE | FALSE
TRUE | FALSE | FALSE | TRUE | FALSE
TRUE | FALSE | TRUE | TRUE | FALSE
TRUE | TRUE | FALSE | TRUE | FALSE
TRUE | FALSE | TRUE | FALSE | FALSE
 |  |  |  |
FALSE | TRUE | TRUE | TRUE | True - unrestricted
FALSE | TRUE | TRUE | FALSE | FALSE
FALSE | TRUE | FALSE | FALSE | FALSE
FALSE | FALSE | FALSE | FALSE | True - no delete
FALSE | FALSE | FALSE | TRUE | True - no delete
FALSE | FALSE | TRUE | TRUE | True - unrestricted
FALSE | TRUE | FALSE | TRUE | True - no delete
FALSE | FALSE | TRUE | FALSE | True - unrestricted

The program and the test-drive logic were then written towards the requirements and the input matrix.

As can be seen from the matrix, tooMany cancels out half the rows. So, only one test case in included to exercise all those rows.

What remains are 8 rows, all without tooMany, and all permutations of the remaining 3 flags.

A test program, lifecycleModule_figleaf_tests_coverage.bsh, is included to drive through the various options in the above table.

To get a coverage report, first run lifecycleModule_figleaf_tests_coverage.bsh. Then browse to any of the resultant html_caseX directories where X is a number from 1 to 11. Locate the index.html file within one of the above directories.

Next locate the lifecycleModule.py entry within the html page and click on it. You will be presented with a summary banner for line coverage as well as a color-coded report showing accessible and inaccessible lines.

#### Example Runs:

#### Here we use all buckets, 25 days to glacier, level two, and forced overwrite of lifecycle policies:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -g 25   -l two -f True  
****************  mvensky-many-folders  ****************
mvensky-many-folders  has a lifecycle policy

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "five-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule1"
        },
        {
            "Status": "Enabled",
            "Prefix": "three-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule2"
        },
        {
            "Status": "Enabled",
            "Prefix": "one-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule3"
        },
        {
            "Status": "Enabled",
            "Prefix": "four-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule4"
        },
        {
            "Status": "Enabled",
            "Prefix": "two-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule5"
        }
    ]
}
****************  mvensky-second  ****************
mvensky-second  has a lifecycle policy

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "root-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-secondRule1"
        }
    ]
}
****************  mvensky-single-level  ****************
mvensky-single-level  has a lifecycle policy

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-single-levelRule1"
        }
    ]
}
****************  mvensky-terraform-state  ****************
mvensky-terraform-state  has a lifecycle policy
For bucket  mvensky-terraform-state  versioning is enabled

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "global/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-terraform-stateRule1"
        }
    ]
}
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "layer-one/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvenskybucketoregonRule1"
        },
        {
            "Status": "Enabled",
            "Prefix": "level-1/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvenskybucketoregonRule2"
        }
    ]
}

```

#### A similar run but now with bucket mvensky-many-folders specified gives similar output, but now restricted to only the named bucket:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -g 25   -l two -f True  -b mvensky-many-folders
****************  mvensky-many-folders  ****************
mvensky-many-folders  has a lifecycle policy

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "five-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule1"
        },
        {
            "Status": "Enabled",
            "Prefix": "three-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule2"
        },
        {
            "Status": "Enabled",
            "Prefix": "one-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule3"
        },
        {
            "Status": "Enabled",
            "Prefix": "four-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule4"
        },
        {
            "Status": "Enabled",
            "Prefix": "two-folder/",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule5"
        }
    ]
}
```

#### With bucket mvensky-many-folders specified and level one:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -g 25   -l one -f True  -b mvensky-many-folders
****************  mvensky-many-folders  ****************
mvensky-many-folders  has a lifecycle policy

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "",
            "Transitions": [
                {
                    "Days": 25,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvensky-many-foldersRule1"
        }
    ]
}
```

#### An attempt to expire a non-versioned bucket:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -e 365   -l one -f True  -b mvensky-single-level
****************  mvensky-single-level  ****************
mvensky-single-level  has a lifecycle policy

No lifecycle policy was applied: make sure bucket, level, forceOverwrite, expire and glacier are set correctly.
Remember you can not set expiration for a bucket without versioning: also expiration must be set for individual buckets
```
#### A versioned bucket:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -e 365   -l one -f True  -b mvenskybucketoregon
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "",
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule1"
        }
    ]
}
```

#### A same  bucket with both glacier and expire:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -e 365 -g 30  -l one -f True  -b mvenskybucketoregon
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule1"
        }
    ]
}
```
#### A same  bucket with both glacier and expire, plus level two:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -e 365 -g 30  -l two -f True  -b mvenskybucketoregon
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "layer-one/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule1"
        },
        {
            "Status": "Enabled",
            "Prefix": "level-1/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule2"
        }
    ]
}
```

#### A same  bucket with both glacier and expire, plus level two, WITHOUT force flag:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -e 365 -g 30  -l two   -b mvenskybucketoregon
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

No lifecycle policy was applied: make sure bucket, level, forceOverwrite, expire and glacier are set correctly.
Remember you can not set expiration for a bucket without versioning: also expiration must be set for individual buckets
```

#### There is a testRun flag; if set to true you can see what will happen WITHOUT actually applying the policies:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -e 365 -g 30  -l two  -f True -b mvenskybucketoregon -t True
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

********* THIS WAS ONLY A TEST RUN; NO POLICIES WERE APPLIED AT THIS TIME  *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "layer-one/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule1"
        },
        {
            "Status": "Enabled",
            "Prefix": "level-1/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule2"
        }
    ]
}
```

#### Same call with testRun flag not set;  here policies get applied:

``` Bash
Yosemite-2:version5 mvensky$ lifecycleModule.py -e 365 -g 30  -l two  -f True -b mvenskybucketoregon
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

********* Here's the new lifecycle that was applied *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "layer-one/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule1"
        },
        {
            "Status": "Enabled",
            "Prefix": "level-1/",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            },
            "ID": "mvenskybucketoregonRule2"
        }
    ]
}
```

#### Here’s what the help screen looks like:

``` Bash
Yosemite-2:git_repo mvensky$ ./lifecycleModule.py
usage: lifecycleModule.py [-h] [--bucket BUCKET] [--level LEVEL]
                          [--glacier GLACIER] [--expire EXPIRE]
                          [--force FORCE] [--testRun TESTRUN]
                          [--specificFolders SPECIFICFOLDERS [SPECIFICFOLDERS ...]]

optional arguments:
  -h, --help            show this help message and exit
  --bucket BUCKET, -b BUCKET
                        name of S3 bucket
  --level LEVEL, -l LEVEL
                        first level folder or prefix name (one/two)
  --glacier GLACIER, -g GLACIER
                        number of days before transition to glacier
  --expire EXPIRE, -e EXPIRE
                        number of days before expiration of affected object(s)
  --force FORCE, -f FORCE
                        if there is a pre-existing policy: force overwrite
                        (True/False)
  --testRun TESTRUN, -t TESTRUN
                        can be run without committing policies to view output
                        only (True/False)
  --specificFolders SPECIFICFOLDERS [SPECIFICFOLDERS ...], -s SPECIFICFOLDERS [SPECIFICFOLDERS ...]
                        enter a list of folders you want rules against add a /
                        to terminate each folder
```

#### A coverage report is available

* To run full report run lifecycleModule_tests_coverage.bsh

* After running the above command a summary can be obtained by running coverage_report.bsh.

* [For an enlightened discussion of code coverage](https://stackoverflow.com/questions/90002/what-is-a-reasonable-code-coverage-for-unit-tests-and-why)

* The "code coverage" is near 100% due to the TDD style of development which can be used when developing in Python. You basically write a few lines of functionality, add some prints and run. Each modification gets exercised in this manner.

* Thus the summary statistics from the above reports do not really reflect what is going on the with the code. All functionality a requested and then some have been fully implemented. An 80 element truth table, cannot be easily automated, rather all functions need be exercised to assure they perform as expected.

#### Here's what it looks like if you specify specific folders, the folders do not have to exist in order to create the rule
``` Bash
Yosemite-2:git_repo mvensky$ lifecycleModule.py -g 15  -l two -t True -f True -b mvenskybucketoregon -s bozo/ pennywise/
****************  mvenskybucketoregon  ****************
mvenskybucketoregon  has a lifecycle policy
For bucket  mvenskybucketoregon  versioning is enabled

********* THIS WAS ONLY A TEST RUN; NO POLICIES WERE APPLIED AT THIS TIME  *********
{
    "Rules": [
        {
            "Status": "Enabled",
            "Prefix": "bozo/",
            "Transitions": [
                {
                    "Days": 15,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvenskybucketoregonRule1"
        },
        {
            "Status": "Enabled",
            "Prefix": "pennywise/",
            "Transitions": [
                {
                    "Days": 15,
                    "StorageClass": "GLACIER"
                }
            ],
            "ID": "mvenskybucketoregonRule2"
        }
    ]
}
```
