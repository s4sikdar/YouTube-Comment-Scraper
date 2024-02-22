#!/usr/bin/env bash

SHORT_DURATION_TESTS=true
LONG_DURATION_TESTS=true
YOUTUBE_SHORT_TESTS=true
REGULAR_YOUTUBE_TESTS=true

function usage() {
cat << EOF
./run_tests.sh [ -h | [ -f | -l ] [ -r | -s ] ]

Description:
This is a bash script that serves as a test harness to run all unit-tests. By default all tests are run for long-duration and
short-duration tests, for both regular YouTube videos and YouTube shorts. By specifying combinations of the options above, we
can specify specific sets of tests that we want to run.

Arguments supported:
-h	Print this help message and exit.

-f	Run the short duration tests only.

-l	Run the long duration tests only.

-r	Run the tests for regular YouTube videos only.

-s	Run the tests for YouTube Shorts only.

Examples:
./run_tests.sh -h		# Print this help message and exit.
./run_tests.sh -f		# Run the short duration tests for YouTube shorts and regular YouTube videos.
./run_tests.sh -l		# Run the long duration tests for YouTube shorts and regular YouTube videos.
./run_tests.sh -r		# Run the tests for regular YouTube videos (both short and long duration).
./run_tests.sh -s		# Run the tests for YouTube Shorts (both short and long duration).
./run_tests.sh -fs		# Run the short duration tests for YouTube Shorts.
./run_tests.sh -ls		# Run the long duration tests for YouTube Shorts.
./run_tests.sh -fr		# Run the short duration tests for regular YouTube videos.
./run_tests.sh -lr		# Run the long duration tests for regular YouTube videos.
EOF
}


OPTIND=1
# The part of the script that parses arguments passed into the command line. The script uses getopts, which should be compatible across platforms,
if [ ${#} -ne 0 ]
then
	while getopts "hflrs" arg_value
	do
		case ${arg_value} in
			h)
				usage
				exit 0
				break
				;;
			l)
				SHORT_DURATION_TESTS=false
				if [ ${LONG_DURATION_TESTS} = "false" ]
				then
					echo "Invalid usage. You cannot specify both the -f flag and the -l flag together" 1>&2
					exit 1
				fi
				;;
			f)
				LONG_DURATION_TESTS=false
				if [ ${SHORT_DURATION_TESTS} = "false" ]
				then
					echo "Invalid usage. You cannot specify both the -f flag and the -l flag together" 1>&2
					exit 1
				fi
				;;
			r)
				YOUTUBE_SHORT_TESTS=false
				if [ ${REGULAR_YOUTUBE_TESTS} = "false" ]
				then
					echo "Invalid usage. You cannot specify both the -r flag and the -s flag together" 1>&2
					exit 1
				fi
				;;
			s)
				REGULAR_YOUTUBE_TESTS=false
				if [ ${YOUTUBE_SHORT_TESTS} = "false" ]
				then
					echo "Invalid usage. You cannot specify both the -r flag and the -s flag together" 1>&2
					exit 1
				fi
				;;
			\?)
				echo "Invalid usage. Run ./run_tests.sh -h for documentation on how to use this script" 1>&2
				exit 1
				;;
		esac
	done
	shift $((${OPTIND}-1))
fi

# Ensure that we are in the virtual environment and all packages are installed before running the tests
source ./env_setup.sh -c

if [ ${LONG_DURATION_TESTS} = "true" ]
then
	if [ ${YOUTUBE_SHORT_TESTS} = "true" ]
	then
		use_correct_python_version -m unittest -v tests.youtube_shorts.test_long_duration_tests.LongDurationShortVideoTests
	fi
	if [ ${REGULAR_YOUTUBE_TESTS} = "true" ]
	then
		use_correct_python_version -m unittest -v tests.youtube_regular.test_long_duration_tests.LongDurationLongVideoTests
	fi
fi

if [ ${SHORT_DURATION_TESTS} = "true" ]
then
	if [ ${YOUTUBE_SHORT_TESTS} = "true" ]
	then
		use_correct_python_version -m unittest -v tests.youtube_shorts.test_short_duration_tests.ShortDurationShortVideoTests
	fi
	if [ ${REGULAR_YOUTUBE_TESTS} = "true" ]
	then
		use_correct_python_version -m unittest -v tests.youtube_regular.test_short_duration_tests.ShortDurationRegularVideoTests
	fi
fi
