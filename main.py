#!/usr/bin/python3
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Andrian Nord
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import sys
import os
import logging
from optparse import OptionParser

def dump(name, obj, level=0):
	indent = level * '\t'

	if name is not None:
		prefix = indent + name + " = "
	else:
		prefix = indent

	if isinstance(obj, (int, float, str)):
		print(prefix + str(obj))
	elif isinstance(obj, list):
		print (prefix + "[")

		for value in obj:
			dump(None, value, level + 1)

		print (indent + "]")
	elif isinstance(obj, dict):
		print (prefix + "{")

		for key, value in obj.items():
			dump(key, value, level + 1)

		print (indent + "}")
	else:
		print (prefix + obj.__class__.__name__)

		for key in dir(obj):
			if key.startswith("__"):
				continue

			val = getattr(obj, key)
			dump(key, val, level + 1)

class MakeFileHandler(logging.FileHandler):
    def __init__(self, filename, *args, **kwargs):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logging.FileHandler.__init__(self, filename, *args, **kwargs)

from datetime import datetime

logger = logging.getLogger('LJD')
logger.setLevel(logging.INFO)

fh = MakeFileHandler(f'logs/{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)


class Main:
	def main(self):
		#parser arguments
		parser = OptionParser()

		parser.add_option("-f", "--file", \
			type="string", dest="file_name", default="", \
			help="decompile file name", metavar="FILE")
		parser.add_option("-o", "--output", \
			type="string", dest="output_file", default="", \
			help="output file for writing", metavar="FILE")
		parser.add_option("-j", "--jitverion", \
			type="string", dest="luajit_version", default="2.1", \
			help="luajit version, default 2.1, now support 2.0, 2.1")
		parser.add_option("-r", "--recursive", \
			type="string", dest="folder_name", default="", \
			help="recursive decompile lua files", metavar="FOLDER")
		parser.add_option("-d", "--dir_out", \
			type="string", dest="folder_output", default="", \
			help="directory to output decompiled lua scripts", metavar="FOLDER")


		(self.options, args) = parser.parse_args()
		basepath=os.path.dirname(sys.argv[0])
		if basepath == "":
			basepath=".";
		sys.path.append(basepath + "/ljd/rawdump/luajit/" + self.options.luajit_version + "/")

		#because luajit version is known after argument parsed, so delay import modules
		import ljd.rawdump.parser
		import ljd.pseudoasm.writer
		import ljd.ast.builder
		import ljd.ast.validator
		import ljd.ast.locals
		import ljd.ast.slotworks
		import ljd.ast.unwarper
		import ljd.ast.mutator
		import ljd.lua.writer

		self.ljd = ljd

		if self.options.folder_name:
			for path, _, filenames in os.walk(self.options.folder_name):
				for file in filenames:
					if file.endswith('.lua'):
						full_path = os.path.join(path, file)

						logger.info(full_path)
						try:
							self.decompile(full_path)
							new_path = os.path.join(self.options.folder_output, os.path.relpath(full_path, self.options.folder_name))
							os.makedirs(os.path.dirname(new_path), exist_ok=True)
							self.write_file(new_path)
							logger.info("Success")
						except KeyboardInterrupt:
							logger.info("Exit")
							return 0
						except:
							logger.info("Exception")
							logger.debug('', exc_info=True)

			return 0

		if self.options.file_name == "":
			print(self.options)
			parser.error("options -f is required")

		self.decompile(self.options.file_name)

		if self.options.output_file:
			self.write_file(self.options.output_file)
		else:
			self.ljd.lua.writer.write(sys.stdout, self.ast)

		return 0

	def write_file(self, file_name):
		with open(file_name, "w", encoding="utf8") as out_file:
			self.ljd.lua.writer.write(out_file, self.ast)


	def decompile(self, file_in):
		header, prototype = self.ljd.rawdump.parser.parse(file_in)

		if not prototype:
			return 1

		# self.ljd.pseudoasm.writer.write(sys.stdout, header, prototype)

		self.ast = self.ljd.ast.builder.build(prototype)

		assert self.ast is not None

		self.ljd.ast.validator.validate(self.ast, warped=True)

		self.ljd.ast.mutator.pre_pass(self.ast)

		# self.ljd.ast.validator.validate(self.ast, warped=True)

		self.ljd.ast.locals.mark_locals(self.ast)

		# ljd.ast.validator.validate(ast, warped=True)

		self.ljd.ast.slotworks.eliminate_temporary(self.ast)

		# self.ljd.ast.validator.validate(ast, warped=True)

		if True:
			self.ljd.ast.unwarper.unwarp(self.ast)

			# self.ljd.ast.validator.validate(ast, warped=False)

			if True:
				self.ljd.ast.locals.mark_local_definitions(self.ast)

				# self.ljd.ast.validator.validate(self.ast, warped=False)

				self.ljd.ast.mutator.primary_pass(self.ast)

				self.ljd.ast.validator.validate(self.ast, warped=False)


if __name__ == "__main__":
	main_obj = Main()
	retval = main_obj.main()
	sys.exit(retval)

# vim: ts=8 noexpandtab nosmarttab softtabstop=8 shiftwidth=8
