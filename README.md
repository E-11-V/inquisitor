# inquisitor
inquisitor is a script that examines pdf files in search of ocr text. It takes a paths.txt file as input, to which all folders to be processed must be added. The script will process all subfolders of any given folder in paths.txt.
Inquisitor examines 3 pages of text: the outcome of the analysis depends on how many of those contain text. If all examined pages contain text the file's path is added to output_ocred.txt; if only some have text, but others don't, it is added to output_doublecheck.txt; if no page contains text, it is added to output_image.txt.
The script resumes its work from where a previous instance left, particularly important in the case of large folders.
