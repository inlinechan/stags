"""Parser module

"""

from clang.cindex import CursorKind
from common import *
from mergedict import merge_recurse_inplace
import clang.cindex
import logging
import os
import sys

function_kind = (
    CursorKind.FUNCTION_DECL,
    CursorKind.CLASS_DECL,
    CursorKind.CXX_METHOD,
    CursorKind.FIELD_DECL,
    CursorKind.CLASS_TEMPLATE,
    CursorKind.FUNCTION_TEMPLATE
)

ref_kind = (CursorKind.DECL_REF_EXPR,
            CursorKind.MEMBER_REF_EXPR,
            CursorKind.TEMPLATE_REF,
            CursorKind.CXX_BASE_SPECIFIER,
            CursorKind.TYPE_REF)

kind_allowed = ref_kind + function_kind

def normalize_path(p):
    return os.path.abspath(p)

def cursor_to_string(cursor, ref_kind):
    "Return cursor info to plain string"
    c = cursor
    string_result = '{}|{}|{}|{}|{}:{}:{}|{}'.format(
        c.is_definition() and 'DEFI' or 'DECL',
        c.kind.name, c.spelling,
        c.type.kind.name,
        c.location.file and normalize_path(c.location.file.name) or None,
        c.location.line, c.location.column, c.get_usr() or 'NoUSR')

    if c.kind in ref_kind and c.referenced:
        r = c.referenced
        assert r
        string_result += ' -> {}|{}|{}|{}:{}:{}|{}'.format(
            r.kind.name, r.spelling,
            r.type.kind.name,
            normalize_path(r.location.file and r.location.file.name or ''),
            r.location.line, r.location.column, r.get_usr() or 'NoUSR')

    return string_result

def get_locus(location):
    assert location.line and location.column
    return '{}:{}'.format(location.line, location.column)

def get_filename_locus(filename, locus):
    return '{}:{}'.format(filename, locus)

def make_sure_file_locus(parsed_dict, filename, locus):
    assert(not os.path.isabs(filename))
    p = parsed_dict
    p.setdefault(filename, {})
    p[filename].setdefault(locus, {})
    p[filename][locus].setdefault(REFS, [])
    return p[filename][locus]

def handle_class_hierarchy(cursor, parsed_dict):
    if cursor.kind != CursorKind.CLASS_DECL:
        return False

    p = parsed_dict
    c = cursor
    usr = c.get_usr()

    def each_inheritance_relation(cursor):
        for base in cursor.get_children():
            if base.kind == CursorKind.CXX_BASE_SPECIFIER:
                yield base.get_definition()

    bases = []
    for base in each_inheritance_relation(cursor):
        base_usr = base.get_usr()
        logging.debug('INHERITANCE: {} -> {}'.format(
            cursor.displayname, base.displayname))
        bases.append(base_usr)
        p.setdefault(base_usr, {})
        p[base_usr].setdefault(CHILD_CLASS, [])
        p[base_usr][CHILD_CLASS].append(usr)

    if not len(bases):
        return False

    p[usr].setdefault(BASE_CLASS, [])
    p[usr][BASE_CLASS].extend(bases)
    return True

def is_ref_is_function_template(cursor, parsed_dict, basedir):
    c = cursor
    p = parsed_dict

    result = False

    if c.kind == CursorKind.MEMBER_REF_EXPR:
        ref_location = c.referenced.location
        ref_locus = get_locus(ref_location)

        filename = ref_location.file.name
        basename = filename
        if basedir:
            idx = filename.find(basedir)
            if idx != -1:
                basename = filename[(idx + len(basedir)):]

        if basename in p and \
           ref_locus in p[basename]:
            ref_usr = p[basename][ref_locus][USR]
            if p[ref_usr][KIND] == CursorKind.FUNCTION_TEMPLATE.name:
                return True
    return result

def get_function_template_usr(cursor, parsed_dict, basedir):
    c = cursor
    p = parsed_dict

    assert(c.kind == CursorKind.MEMBER_REF_EXPR)

    ref_location = c.referenced.location
    ref_locus = get_locus(ref_location)

    if basedir:
        filename = ref_location.file.name
        idx = filename.find(basedir)
        if idx != -1:
            basename = filename[(idx + len(basedir)):]

    assert(not os.path.isabs(basename))
    ref_usr = p[basename][ref_locus][USR]
    assert(ref_usr)
    return ref_usr

def parse_cursor(cursor, parsed_dict, ref_kind, basedir):
    c = cursor
    p = parsed_dict

    filename = normalize_path(c.location.file.name)
    assert(basedir)
    basename = filename
    if basedir:
        idx = filename.find(basedir)
        if idx != -1:
            basename = filename[(idx + len(basedir)):]

    locus = get_locus(c.location)
    usr = c.get_usr()

    filename_locus = get_filename_locus(basename, locus)

    if c.kind in ref_kind:
        assert not c.get_usr()
        p.setdefault(basename, {})
        assert(not basename.startswith(basedir))
        file_dict = p[basename]
        assert c.location.line and c.location.column
        is_definition = c.is_definition()
        if c.referenced and c.referenced.get_usr():
            assert c.referenced.get_usr()
            entry = {}
            if c.kind == CursorKind.TEMPLATE_REF and \
               c.referenced.kind == CursorKind.CLASS_TEMPLATE:
                entry[TEMPLATE_USR] = c.referenced.get_usr()
            elif is_ref_is_function_template(c, p, basedir):
                entry[TEMPLATE_USR] = get_function_template_usr(c, p, basedir)
            else:
                entry[REF_USR] = c.referenced.get_usr()
            if locus in file_dict:
                merge_recurse_inplace(file_dict[locus], entry)
            else:
                file_dict[locus] = entry

            # update reference in usr
            r = c.referenced
            r_usr = r.get_usr()
            if TEMPLATE_USR in entry:
                r_usr = entry[TEMPLATE_USR]

            p.setdefault(usr, {})
            filename_locus = get_filename_locus(basename, locus)
            entry = {
                REFS: [filename_locus]
            }
            if c.kind == CursorKind.CXX_BASE_SPECIFIER:
                entry[KIND] = c.kind.name
                entry[SPELL] = c.spelling

            if r_usr in p:
                merge_recurse_inplace(p[r_usr], entry)
            else:
                p[r_usr] = entry

    if c.kind in function_kind:
        # assert usr
        entry = {
            c.is_definition() and DEFI or DECL: filename_locus,
            KIND: c.kind.name,
            SPELL: c.spelling,
            TYPE: c.type.kind.name,
            REFS: [],
        }
        if usr in p:
            merge_recurse_inplace(p[usr], entry)
        else:
            p[usr] = entry

        p.setdefault(basename, {})
        assert(not basename.startswith(basedir))
        file_dict = p[basename]
        locus_entry = {
            USR: usr
        }
        if locus in file_dict:
            merge_recurse_inplace(file_dict[locus], locus_entry)
        else:
            file_dict[locus] = locus_entry

        result = handle_class_hierarchy(c, p)

def parse(filename, *args, **kwargs):
    index = clang.cindex.Index.create()

    parsed_dict = {}

    filename = os.path.abspath(filename)
    basedir = kwargs.get('basedir', None)

    try:
        tu = index.parse(filename, args)
    except clang.cindex.TranslationUnitLoadError as e:
        logging.warning(e)
        return

    debug = kwargs.get('debug', False)

    for cursor in tu.cursor.walk_preorder():
        if cursor.kind in kind_allowed:
            if not cursor.location.file:
                logging.debug('Cursor without location {}: {}'.format(
                    filename, cursor_to_string(cursor, ref_kind)))
            else:
                cursor_filename = os.path.normpath(cursor.location.file.name)
                if cursor_filename.startswith('/usr/include/c++'):
                    continue

                parse_cursor(cursor, parsed_dict, ref_kind, basedir)
        if debug:
            logging.info(cursor_to_string(cursor, ref_kind))

    return parsed_dict

if __name__ == '__main__':
    libclang_set_library_file()
    logging.basicConfig(level=logging.INFO)
    assert len(sys.argv) >= 2
    filename = sys.argv[1]
    args = sys.argv[2:]
    parsed_dict = parse(filename, *args)

    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    print('result len(key): {}'.format(len(parsed_dict.keys())))
    print(pp.pformat(parsed_dict))
