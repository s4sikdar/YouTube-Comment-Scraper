#!/usr/bin/env bash

source ./setup_scripts/correct_python.sh
source ./setup_scripts/find_os_and_platform.sh

# The function uses the python script get_webdriver.py to download the latest chromedriver binary available for google chrome.
# From there it extracts the chromedriver binary only from the zip file using the unzip command (if possible). It then prints
# the file path for the extracted binary relative to where the zip file is downloaded. The script path to the get_webdriver.py script must be passed in.
function get_latest_chromedriver() {
	python_script_path="${1}"
	tempfile=$(mktemp)
	#error_output_file=$(mktemp)
	# Since standard error is redirected to /dev/null, a non-zero exit code from the get_platform function (something going wrong) will result in
	# platform being an empty string.
	platform=$(get_platform 2> /dev/null)
	if [ -z "${platform}" ]
	then
		# Show standard error only. Since it is not in a subshell this time, the script should exit.
		rm ${tempfile}
		get_platform 1> /dev/null
	fi
	# Since standard error is redirected to /dev/null, a non-zero exit code from the command in the subshell will result in
	# platform being an empty string. Proceed further if zip_fname has non-zero length only.
	zip_fname=$(use_correct_python_version "${python_script_path}" --platform="${platform}" 2> /dev/null)
	if [ "${zip_fname}" ]
	then
		# Test that we have the unzip command installed
		unzip -v &> /dev/null
		if [ ${?} -ne 0 ]
		then
			echo "The file ${zip_fname} was downloaded but the unzip is not supported. The script will exit with an error code of 1." 1>&2
			echo "You will need to manually unzip the chromedriver zip file, take out the chromedriver binary, and install it in your PATH environment variable." 1>&2
			rm ${tempfile}
			exit 1
		fi
		# unzil -ql ${zip_filename} shows information on the what is inside of the zip file, including the file paths.
		# The first 2 and last 2 lines are for decoration. So the actual line count is the line count from unzip -ql "file name" minus 4
		unzip_line_count=$(unzip -ql "${zip_fname}" 2> /dev/null | wc -l 2> /dev/null)
		line_count_outside_last_2=$((${unzip_line_count} - 2))
		actual_file_count=$((${line_count_outside_last_2} - 2))
		# get all files in the zip file that are not the chromedriver binary and print them to a tempfile.
		unzip -ql ${zip_fname} 2> /dev/null | head -n ${line_count_outside_last_2} 2> /dev/null | tail -n ${actual_file_count} 2> /dev/null | awk '!/\/chromedriver(.exe)?$/ {print $NF}' > ${tempfile} 2> /dev/null
		tempfile_char_count=$(wc -c ${tempfile} | awk '{ print $1 }' 2> /dev/null)
		if [[ ${tempfile_char_count} -eq 0 ]]
		then
			echo "Something when wrong when trying to unzip. The script will exit with an error code of 1." 1>&2
			echo "You will have to manually unzip the chromedriver zip file, take out the chromedriver binary and add it to your PATH environment variable." 1>&2
			rm ${tempfile}
			exit 1
		else
			# Use the tempfile contents as input for files unzip should ignore when unzipping files (specified with the -x flag in the unzip command)
			unzip -ql ${zip_fname} 2> /dev/null | head -n ${line_count_outside_last_2} 2> /dev/null | tail -n ${actual_file_count} 2> /dev/null | awk '/\/chromedriver(.exe)?$/ {print $NF}'
			cat ${tempfile} | xargs unzip -q "${zip_fname}" -x
		fi
		echo "" > ${tempfile}
		rm ${tempfile}
	else
		echo "Was unable to download the latest chromedriver binary for some reason. Exiting with an error code of 1." 1>&2
		rm ${tempfile}
		exit 1
	fi
}

# find_and_install_chromedriver gets the chromedriver executable, and puts it into ~/bin/. Everything else is removed.
# Three arguments are taken:
# 1) ${1} contains the absolute path to the python script
# 2) ${2} contains the executable name
# 3) ${3} contains the name of the zip file
# Requires: when the function is called, you must be in ~/bin/
function download_and_move_chromedriver_locally() {
	# get_latest_chromedriver prints out the path to the chromedriver executable relative to where the zipfile is.
	# If the path is different (i.e. chromedriver is in another nested directory) copy the executable into ~/bin/ and remove the original different path (as well as everything else).
	# Otherwise, do nothing to the path to the chromedriver executable. Also we remove the zip file.
	python_script_path="${1}"
	executable_name="${2}"
	zip_file_name="${3}"
	chromedriver_executable_path=$(get_latest_chromedriver "${python_script_path}" 2> /dev/null)
	#chromedrivers_in_bin_dir=$(find -maxdepth 1 -type f -iname "${executable_name}" 2> /dev/null)
	num_fields_seprated_by_slash=$(echo "${chromedriver_executable_path}" | awk -F / '{ print NF }')
	directory_name=$(echo "${chromedriver_executable_path}" | awk -F / '{ print $1 }')
	# We don't know the file structure inside the zip file until we use the unzip command.
	# The chromedriver executable could be nested in multiple subdirectories. So if the number of fields
	# separated by a forward slash is greater than 1, then we know that the executable is in a subdirectory, and we need to copy the original path to the chromedriver
	# executable and put it in the main ~/bin/ directory. Then we remove the directory name for the original chromedriver executable path (if applicable), and the zipfile.
	if [[ ${num_fields_seprated_by_slash} -gt 1 ]]
	then
		# In the special case that we have the executable name being the same as the directory name, we create a placeholder
		# directory, copy the executable there, and remove the original directory with the same name as the executable. Then copy the executable
		# out of the placeholder directory and into ~/bin/. Then remove the placeholder directory.
		if [ "${directory_name}" = "${executable_name}" ]
		then
			echo "Chromedriver executable is in ${HOME}/bin/${chromedriver_executable_path}. Moving executable to ${HOME}/bin/ and removing both directory ${HOME}/bin/${directory_name}/ and ${zip_file_name}."
			num=1
			placeholder_dir="testdir${num}"
			while [ -d "${placeholder_dir}" ]
			do
				num=$($(${num} + 1))
				placeholder_dir="testdir${num}"
			done
			mkdir "${placeholder_dir}"
			cp "./${chromedriver_executable_path}" "./${placeholder_dir}/"
			rm -r "./${directory_name}/"
			cp "./${placeholder_dir}/${executable_name}" "./${executable_name}"
			rm -r "./${placeholder_dir}/"
		else
			echo "Chromedriver executable is in ${HOME}/bin/${chromedriver_executable_path}. Moving executable to ${HOME}/bin/ and removing both directory ${HOME}/bin/${directory_name}/ and ${zip_file_name}."
			cp "${chromedriver_executable_path}" "./${executable_name}"
			rm -r "./${directory_name}/"
		fi
	fi
	echo "Chromedriver executable is installed in ${HOME}/bin/."
	rm "${zip_file_name}"
}

# Function to check if ~/bin/ is in your $PATH environment variable. Credit to the source below:
# https://stackoverflow.com/questions/1396066/detect-if-path-has-a-specific-directory-entry-in-it
# If ~/bin/ dir is not in your path variable, it will add it for you and this is exported to your current bash session
# (assuming when you use this function, you call the script with the source command). You may have to manually remove this directory from your path to undo it.
function add_bin_dir_in_home_to_path() {
	local confirmation_text=''
	if [[ ":${PATH}:" != *":${HOME}/bin:"* ]]
	then
		echo "${HOME}/bin/ is not in your path directory. The script will add this directory to your PATH environment variable."
		echo "Would you like to proceed with this? Enter 'y' to confirm permission or 'n' to deny permission."
		read confirmation_text
		while [ "${confirmation_text}" != 'y' -a "${confirmation_text}" != 'n' ]
		do
			echo "Invalid input. Enter 'y' to confirm permission, 'n' to deny permission."
			read confirmation_text
		done
		if [ "${confirmation_text}" = 'y' ]
		then
			export PATH="${HOME}/bin:${PATH}"
			echo "Added ${HOME}/bin/ to your PATH environment variable."
		else
			echo "The chromedriver binary is in ${HOME}/bin/. This is not in your PATH environment variable."
			echo "You need to transfer the executable to a directory in your PATH environment variable."
		fi
	fi
}

# The function that ensures the following:
# 1) A ~/bin/ directory exists and it is in your $PATH variable. Otherwise create the ~/bin/ directory if necessary, and try to add it to the user's $PATH.
# 2) Inside the ~/bin/ directory is the latest stable version of chromedriver (platform specific executable). Otherwise download the latest version.
function find_and_install_chromedriver() {
	latest_stable_version_endpoint='https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE'
	latest_stable_version=$(curl -s "${latest_stable_version_endpoint}" 2> /dev/null)
	linux_64_zip_name='chromedriver-linux64.zip'
	mac_arm64_zip_name='chromedriver-mac-arm64.zip'
	mac_x64_zip_name='chromedriver-mac-x64.zip'
	win32_zip_name='chromedriver-win32.zip'
	win64_zip_name='chromedriver-win64.zip'
	python_script_path="${project_path}/get_webdriver.py"
	platform_name=$(get_platform)
	executable_name='chromedriver'
	zip_file_name=''
	project_path=$(pwd)

	cd ${HOME}
	case ${platform_name} in
		win32*)
			executable_name='chromedriver.exe'
			zip_file_name="${win32_zip_name}"
			;;
		win64*)
			executable_name='chromedriver.exe'
			zip_file_name="${win64_zip_name}"
			;;
		linux64*)
			executable_name='chromedriver'
			zip_file_name="${linux_64_zip_name}"
			;;
		mac-arm64*)
			executable_name='chromedriver'
			zip_file_name="${mac_arm64_zip_name}"
			;;
		mac-x64*)
			executable_name='chromedriver'
			zip_file_name="${mac_x64_zip_name}"
			;;
		*)
			echo "Unknown platform that does not support chromedriver. Exiting with an error code of 2." 1>&2
			exit 2
			;;
	esac
	if [ -d "bin" ]
	then
		cd bin/
		if [ -s "${executable_name}" ]
		then
			local_chromedriver_version=$(./${executable_name} --version 2> /dev/null | awk '{ print $2 }' 2> /dev/null)
			# if local_chromedriver_version is an empty string, or does not equal latest stable version, then remove the local chromedriver executable and download the latest one.
			if [ -z "${local_chromedriver_version}" -o "${local_chromedriver_version}" != "${latest_stable_version}" ]
			then
				echo "Local chromedriver version is not the latest stable version, or the version could not be gathered from the file, or the latest stable version cannot be gathered."
				echo "In all cases, something is wrong. Downloading the latest version of chromedriver and removing the existing file with the same name as the executable name."
				rm "${executable_name}"
				download_and_move_chromedriver_locally "${python_script_path}" "${executable_name}" "${zip_file_name}"
			fi
		else
			echo "bin/ directory exists in ${HOME} but there is no \"${executable_name}\" binary executable in bin/. Downloading and installing it now."
			download_and_move_chromedriver_locally "${python_script_path}" "${executable_name}" "${zip_file_name}"
		fi
	else
		echo "bin directory is not there. Making a bin directory in ${HOME} and adding the chromedriver binary executable there."
		mkdir bin; cd bin/
		download_and_move_chromedriver_locally "${python_script_path}" "${executable_name}" "${zip_file_name}"
	fi
	# Only add the bin/ dir to your PATH environment variable once you have downloaded the latest chromedriver binary.
	add_bin_dir_in_home_to_path
}
