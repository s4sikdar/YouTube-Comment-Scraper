#!/usr/bin/env bash

# A function to try and find out whether to use python or python3. Some computers may have python point to python3, others have python point to python2 (so you have to specify python3). Then run the according
# python command with the other arguments passed in after (i.e. can use this function to run python scripts as you otherwise would by running "use_correct_python_version script.py -a 2 -b 3 ..."
function use_correct_python_version() {
	python_version=0
	/usr/bin/env python --version &> /dev/null
	if [[ ${?} -eq 0 ]]
	then
		python_version=$(/usr/bin/env python --version 2> /dev/null | awk '{ print $NF }' 2> /dev/null | awk -F . '{ print $1 }' 2> /dev/null)
		if [[ ${python_version} -eq 3 ]]
		then
			/usr/bin/env python "${@}"
		else
			/usr/bin/env python3 --version &> /dev/null
			if [[ ${?} -eq 0 ]]
			then
				/usr/bin/env python3 "${@}"
			else
				echo "Python3 not installed." 1>&2
				exit 2
			fi
		fi
	else
		/usr/bin/env python3 --version &> /dev/null
		if [[ ${?} -eq 0 ]]
		then
			/usr/bin/env python3 "${@}"
		else
			echo "Python not installed." 1>&2
			exit 2
		fi
	fi
}
