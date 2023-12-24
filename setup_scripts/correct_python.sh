#!/usr/bin/env bash

# Some users have "python" pointing directly to python3, and they don't actually have python3 as a command on their machine.
# Other users have "python3" pointing to python3 as a command, but not "python" as a command (or if python is installed, it
# points to python2, which will not work).
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
				echo "Python not installed." &>2
				exit 2
			fi
		fi
	else
		/usr/bin/env python3 --version &> /dev/null
		if [[ ${?} -eq 0 ]]
		then
			/usr/bin/env python3 "${@}"
		else
			echo "Python not installed." &>2
			exit 2
		fi
	fi
}

