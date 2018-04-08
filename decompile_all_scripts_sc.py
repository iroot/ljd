import os
import sys
import shutil

import ljd.rawdump.parser
import ljd.pseudoasm.writer
import ljd.ast.builder
import ljd.ast.validator
import ljd.ast.locals
import ljd.ast.slotworks
import ljd.ast.unwarper
import ljd.ast.mutator
import ljd.lua.writer


def find_all_lua_scripts():
    walk_dir = sys.argv[1]

    print('walk_dir = ' + walk_dir)

    # If your current working directory may change during script execution, it's recommended to
    # immediately convert program arguments to an absolute path. Then the variable root below will
    # be an absolute path as well. Example:
    # walk_dir = os.path.abspath(walk_dir)
    # print('walk_dir (absolute) = ' + os.path.abspath(walk_dir))

    looked_dirs = ['gamedata', 'levels', 'scripts', 'ui\scripts']

    with open('lua_scripts.txt', 'w') as lua_scripts:
        for path in looked_dirs:
            new_path = os.path.join(walk_dir, path)
            for root, subdirs, files in os.walk(new_path):
                # print('--\nroot = ' + root)
                # print('list_file_path = ' + list_file_path)
                for filename in files:
                    if filename.endswith('.lua') and not filename.endswith('.dec.lua'):
                        file_path = os.path.join(root, filename)
                        # print('\t- file %s (full path: %s)' % (filename, file_path))
                        lua_scripts.write(file_path + '\n')


def decompile_all_scripts():
    with open('lua_scripts.txt', 'r') as lua_scripts:
        for file_in in lua_scripts.readlines():
            if file_in:
                file_in = file_in[:-1]
                file_out = os.path.splitext(file_in)[0] + '.dec.lua'
                print('Input file:', file_in)
                with open(file_out, 'w') as output_script:
                    try:
                        decompile_script(file_in, output_script)
                    except:
                        pass
                print('Output file:', file_out)


def decompile_script(file_in, file_out):
    header, prototype = ljd.rawdump.parser.parse(file_in)

    if not prototype:
        return 1

    # TODO: args
    # ljd.pseudoasm.writer.write(sys.stdout, header, prototype)

    ast = ljd.ast.builder.build(prototype)

    assert ast is not None

    ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.mutator.pre_pass(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.locals.mark_locals(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    ljd.ast.slotworks.eliminate_temporary(ast)

    # ljd.ast.validator.validate(ast, warped=True)

    if True:
        ljd.ast.unwarper.unwarp(ast)

        # ljd.ast.validator.validate(ast, warped=False)

        if True:
            ljd.ast.locals.mark_local_definitions(ast)

            # ljd.ast.validator.validate(ast, warped=False)

            ljd.ast.mutator.primary_pass(ast)

            ljd.ast.validator.validate(ast, warped=False)

    ljd.lua.writer.write(file_out, ast)

    return 0


def move_files():
    walk_dir = sys.argv[1]

    print('walk_dir = ' + walk_dir)

    for root, subdirs, files in os.walk(walk_dir):
        # print('--\nroot = ' + root)
        # print('list_file_path = ' + list_file_path)
        for filename in files:
            if filename.endswith('.xml') or filename.endswith('.dec.lua'):
                old_path = os.path.join(root, filename)
                new_root = root.replace('data.unpack', 'data.scripts')
                new_path = os.path.join(new_root, filename)
                os.makedirs(new_root, exist_ok=True)
                shutil.copy(old_path, new_path)
                # print('\t- file %s (full path: %s)' % (filename, file_path))


if __name__ == '__main__':
    find_all_lua_scripts()
    decompile_all_scripts()
    move_files()
