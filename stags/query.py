"""Query module

"""

from common import *
from enum import Enum           # pip install enum34
from storage import ShelveStorage
import clang.cindex
import logging
import os
import parser
import pygraphviz
import sys

def make_locus(line, column):
    return '{}:{}'.format(line, column)

class Query(Enum):
    Definition         = 0
    Declaration        = 1
    Reference          = 2
    ReferenceInherit   = 3
    SymbolInfo         = 4
    ClassHierarchy     = 5

def fullpath(filename, basedir):
    assert(filename and not os.path.isabs(filename))
    return basedir + filename

def basename(func, *args, **kwargs):
    def start(*args, **kwargs):
        filename, locus, parsed_dict = args

        basedir = parsed_dict['basedir']
        assert(basedir)
        idx = filename.find(basedir)

        if idx != -1:
            filename = filename[(idx + len(basedir)):]

        return func(filename, locus, parsed_dict, **kwargs)
    return start

@basename
def get_any_usr(filename, locus, parsed_dict):
    assert(not os.path.isabs(filename))
    target = parsed_dict[filename][locus]
    usr = target.get(USR, None)
    ref_usr = target.get(REF_USR, None)
    return usr or ref_usr

@basename
def get_template_usr(filename, locus, parsed_dict):
    assert(not os.path.isabs(filename))
    target = parsed_dict[filename][locus]
    return target.get(TEMPLATE_USR, None)

@basename
def query_decl_and_defi(filename, locus, parsed_dict):
    assert(not os.path.isabs(filename))
    any_usr = get_any_usr(filename, locus, parsed_dict)
    defi = parsed_dict[any_usr].get(DEFI, None)
    decl = parsed_dict[any_usr].get(DECL, None)
    return (decl, defi)

@basename
def query_template_decl_and_defi(filename, locus, parsed_dict):
    assert(not os.path.isabs(filename))
    template_usr = get_template_usr(filename, locus, parsed_dict)
    defi = parsed_dict[template_usr].get(DEFI, None)
    decl = parsed_dict[template_usr].get(DECL, None)
    return (decl, defi)

@basename
def query_definition(filename, locus, parsed_dict):
    decl, defi = query_decl_and_defi(filename, locus, parsed_dict)
    if decl or defi:
        return defi or decl
    else:
        decl, defi = query_template_decl_and_defi(filename, locus, parsed_dict)
        return defi or decl

@basename
def query_declaration(filename, locus, parsed_dict):
    decl, defi = query_decl_and_defi(filename, locus, parsed_dict)
    if decl or defi:
        return decl or defi
    else:
        decl, defi = query_template_decl_and_defi(filename, locus, parsed_dict)
        return decl or defi

@basename
def query_reference(filename, locus, parsed_dict):
    any_usr = get_any_usr(filename, locus, parsed_dict) or \
              get_template_usr(filename, locus, parsed_dict)
    assert(REFS in parsed_dict[any_usr])

    # TODO: call recursive if necessary
    return parsed_dict[any_usr][REFS]

@basename
def query_reference_inherit(filename, locus, parsed_dict):
    any_usr = get_any_usr(filename, locus, parsed_dict) or \
              get_template_usr(filename, locus, parsed_dict)
    assert(REFS in parsed_dict[any_usr])

    locations = []
    if KIND in parsed_dict[any_usr] and parsed_dict[any_usr][KIND] == 'CXX_METHOD':
        def visit_hierarchy(usr, parsed_dict, visited_nodes):
            p = parsed_dict
            if SPELL in p[usr]:
                logging.debug('visit_hierarchy: {}'.format(p[usr][SPELL]))
            # assert(p[usr][KIND] == 'CLASS_DECL')

            for base in p[usr].get(BASE_CLASS, []):
                if base in visited_nodes:
                    continue
                visited_nodes.add(base)
                if SPELL in p[usr] and SPELL in p[base]:
                    logging.debug('Processing {} - > {}'.format(p[usr][SPELL], p[base][SPELL]))
                yield base
                for node in visit_hierarchy(base, p, visited_nodes):
                    yield node

            for derived in p[usr].get(CHILD_CLASS, []):
                if derived in visited_nodes:
                    continue
                visited_nodes.add(derived)
                if SPELL in p[derived] and SPELL in p[usr]:
                    logging.debug('Processing {} - > {}'.format(p[derived][SPELL], p[usr][SPELL]))
                yield derived
                for node in visit_hierarchy(derived, p, visited_nodes):
                    yield node

        # logging.info('parsed_dict[any_usr][KIND]: {}'.format(parsed_dict[any_usr][KIND]))
        method_position = any_usr.rfind('@F')
        class_usr = any_usr[:method_position]
        method_name = any_usr[method_position:]
        assert(len(class_usr) and parsed_dict[class_usr])

        visited_nodes = set()
        for node in visit_hierarchy(class_usr, parsed_dict, visited_nodes):
            node_usr = node + method_name
            if node_usr in parsed_dict:
                locations.extend(parsed_dict[node_usr][REFS])
    locations.extend(parsed_dict[any_usr][REFS])

    return locations

@basename
def query_symbol_info(filename, locus, parsed_dict):
    any_usr = get_any_usr(filename, locus, parsed_dict)
    template_usr = get_template_usr(filename, locus, parsed_dict)
    any_usr = any_usr or template_usr
    assert(not os.path.isabs(filename))
    target = parsed_dict[filename][locus]

    return {'{}:{}'.format(filename, locus): target, any_usr: parsed_dict[any_usr]}

@basename
def query_class_hierarchy(filename, locus, parsed_dict, **kwargs):
    any_usr = get_any_usr(filename, locus, parsed_dict)
    # assert(not '@F' in any_usr)
    export_as = kwargs.get('export_as', 'png')

    if not parsed_dict[any_usr][KIND] in ('TYPE_REF', 'CLASS_DECL', 'CXX_BASE_SPECIFIER'):
        return None

    def visit_hierarchy(usr, parsed_dict, visited_edges):
        p = parsed_dict
        logging.debug('visit_hierarchy: {}'.format(p[usr][SPELL]))
        assert(p[usr][KIND] in ('CLASS_DECL', 'TYPE_REF', 'CXX_BASE_SPECIFIER'))

        for base in p[usr].get(BASE_CLASS, []):
            edge = (usr, base)
            if edge in visited_edges:
                continue
            visited_edges.add(edge)
            logging.debug('Processing {} - > {}'.format(p[usr][SPELL], p[base][SPELL]))
            yield p[usr][SPELL], p[base][SPELL]
            for edge in visit_hierarchy(base, p, visited_edges):
                yield edge

        for derived in p[usr].get(CHILD_CLASS, []):
            edge = (derived, usr)
            if edge in visited_edges:
                continue
            visited_edges.add(edge)
            logging.debug('Processing {} - > {}'.format(p[derived][SPELL], p[usr][SPELL]))
            yield p[derived][SPELL], p[usr][SPELL]
            for edge in visit_hierarchy(derived, p, visited_edges):
                yield edge

    def generate_class_hierarachy(usr, parsed_dict, export_as="text", output_filename=None):
        visited_edges = set()
        pairs = set()
        for derived, base in visit_hierarchy(usr, parsed_dict, visited_edges):
            pairs.add((derived, base))

        if export_as == "text":
            return pairs

        def draw(graph, output_filename):
            graph.layout(prog='dot')
            graph.draw(output_filename)

        graph = pygraphviz.AGraph(directed=True, rankdir='BT')
        graph.node_attr['shape'] = 'record'
        graph.node_attr['fontname'] = 'Helvetica'
        graph.node_attr['fontsize'] = '10'
        graph.edge_attr['arrowhead'] = 'onormal'
        graph.add_node(parsed_dict[any_usr][SPELL],
                       color='black',
                       fillcolor='grey75',
                       style='filled')
        for derived, base in pairs:
            edge = (derived, base)
            graph.add_edge(edge)

        if not output_filename:
            output_filename = 'class_hierarchy_{}.png'.format(parsed_dict[any_usr][SPELL])
            output_filename = output_filename.replace(' ', '_')

            basedir = parsed_dict['basedir']
            output_filename = os.path.join(basedir, output_filename)

        draw(graph, output_filename)
        return os.path.abspath(output_filename)

    return generate_class_hierarachy(any_usr, parsed_dict, export_as)

def query(query_type, location, parsed_dict):
    if not location:
        if query_type == Query.Reference:
            return []
        else:
            return None
    filename, line, column = location.split(':')
    line = int(line)
    column = int(column)
    assert filename
    assert line
    assert column
    locus = make_locus(line, column)

    funcs = {
        Query.Definition:       query_definition,
        Query.Declaration:      query_declaration,
        Query.Reference:        query_reference,
        Query.ReferenceInherit: query_reference_inherit,
        Query.SymbolInfo:       query_symbol_info,
        Query.ClassHierarchy:   query_class_hierarchy
    }

    return funcs[query_type](filename, locus, parsed_dict)

def location_with_text(location, basedir):
    filename, line, column = location.split(':')
    line = int(line)
    column = int(column)

    fullpath = basedir + filename
    fulllocation = '{}:{}:{}'.format(fullpath, line, column)

    assert os.path.exists(fullpath)
    with open(fullpath) as f:
        text = ''
        for i, item in enumerate(f):
            if i + 1 == line:
                text = item.rstrip()
                break
        return '{}:{}'.format(fulllocation, text)

if __name__ == '__main__':
    libclang_set_library_file()
    logging.basicConfig(level=logging.INFO)
    assert len(sys.argv) >= 4
    filename = sys.argv[1]
    query_type = sys.argv[2]
    query_location = sys.argv[3]
    if filename.endswith('.db'):
        parsed_dict = ShelveStorage(filename)
    else:
        parsed_dict = parser.parse(filename)

    import os

    basedir = parsed_dict['basedir']
    if query_type == Query.SymbolInfo:
        basedir = None
    locations = query(Query[query_type], query_location, parsed_dict)
    assert locations
    if isinstance(locations, list):
        # Sort order by line as integer first and by filename later to keep ordering
        # https://wiki.python.org/moin/HowTo/Sorting#Maintaining_Sort_Order
        unique_locations = list(set(locations))
        line_sorted = sorted(unique_locations, key=lambda x: int(x.split(':')[1]))
        filename_sorted = sorted(line_sorted, key=lambda x: x.split(':')[0])
        for location in filename_sorted:
            print(location_with_text(location, basedir))
    elif isinstance(locations, dict):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(locations)
    else:
        if query_type == 'ClassHierarchy':
            print(locations)
        else:
            print(location_with_text(locations, basedir))

