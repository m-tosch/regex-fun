import re

# TODO
# input with no vhdl content? if group(1) else None   and return?
# maybe more detailed "classes" e.g. Entity(), Package() with parser methods
# install coverage package https://pypi.org/project/coverage/


def _get_raw_vhdl(buffer):
    """
    Removes all VHDL comments and substitutes all whitespaces/tabs/line breaks
    with a single whitespace
    """
    # remove all VHDL comments
    # (                 begin of capture group
    #     \s*           zero or more whitespaces
    #     --            two dashes
    # )                 end of capture group
    # .*                any character zero or more times
    # \n?               line break. lazy evaluation
    buffer = re.sub(r"(\s*--).*\n?", "", buffer, flags=re.MULTILINE)
    # substitute all tabs, newlines, whitespaces with a single whitespace
    # the .strip() removes any leading and trailing whitespaces
    # \s+               one ore more whitespaces
    buffer = re.sub(r"\s+", " ", buffer).strip()
    return buffer


def get_entity(buffer):
    # [^- ]             anything that is NOT a dash or whitespace
    # +                 one or more times
    # \s*               zero or more whitespaces
    # (                 begin of capture group---------------------------ENTITY
    #     entity        "entity"
    #     \s+           one or more whitespaces
    #     .+            any character one or more times
    #     \s+           one or more whitespaces
    #     is            "is"
    #     .*            any character zero or more times (->generics and ports)
    #     end           "end"
    #     \s+           one or more whitespaces
    #     .*            any character zero or more times
    #     ;             semicolon
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # architecture      "architecture"
    m = re.search(
        r"[^- ]+\s*(entity\s+.+\s+is.*end\s+.*;)\s*architecture",
        _get_raw_vhdl(buffer),
        flags=re.IGNORECASE,
    )
    entity = m.group(1)
    # generics = get_entity_generics(entity)
    # ports = get_entity_ports(entity)
    # return generics, ports
    return entity


def get_ports(buffer):
    # TODO
    # port names can be on the same line but separated by a comma
    # clk, reset : in std_logic;
    # instead of
    # clk : in std_logic;
    # reset : in std_logic;

    # extract the entity string if it exists
    entity = get_entity(buffer)

    # (                 begin of capture group---------------------ENTITY PORTS
    #     port          "port"
    #     \s*           zero or more whitespaces
    #     \(            opening parenthesis
    #     .*            any character zero or more times
    #     \)            closing parenthesis
    #     \s*           zero or more whitespaces
    #     ;             semicolon
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # end               "end"
    m = re.search(r"(port\s*\(.*\)\s*;)\s*end", entity, flags=re.IGNORECASE)
    port_str = m.group(1)
    print(port_str)

    # port variable names
    # (                 begin of capture group----------------------------NAMES
    #     [a-z]         lowercase letter (identifiers must begin with that)
    #     [a-z_0-9,]    lowercase letter/underscore/digit or comma
    #     *             zero or more times
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # :                 double colon
    port_names = re.findall(
        r"([a-z][a-z_0-9,]*)\s*:", port_str, flags=re.IGNORECASE
    )

    # port directions (in, out, inout)
    # :                 double colon
    # \s*               zero or more whitespaces
    # (                 begin of capture group------------------------DIRECTION
    #     [a-z]{2,}     lowercase letter. two or more times (shortest is "in")
    # )                 end of capture group
    # \s+               one or more whitespaces
    port_dirs = re.findall(
        r":\s*([a-z]{2,})\s+", port_str, flags=re.IGNORECASE
    )

    # port types (e.g. std_logic)
    # :                 double colon
    # \s*               zero or more whitespaces
    # [a-z]{2,}         lowercase letter. two or more times
    # \s+               one or more whitespaces
    # (                 begin of capture group
    #     .+?           any character one or more times. lazy evaluation
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # (?:               begin of non-capture group------------------------TYPES
    #     ;             semicolon
    #     |             OR
    #     (?:           begin of non-capture group
    #         \)        closing parenthesis
    #         \s*       zero or more whitespaces
    #         ;         semicolon
    #         \s*       zero or more whitespaces
    #         end       "end"
    #     )             end of non-capture group
    # )                 end of non-capture group
    port_types = re.findall(
        r":\s*[a-z]{2,}\s+(.+?)\s*(?:;|(?:\)\s*;\s*end))",
        port_str,
        flags=re.IGNORECASE,
    )

    # collect list of indices with , and their count
    ll = [(i, n.count(",") + 1) for i, n in enumerate(port_names) if "," in n]
    indices = list(list(zip(*ll))[0])
    count = list(list(zip(*ll))[1])

    # correct port names list (expand)
    for i, pn in enumerate(port_names):
        if "," in pn:
            variables = pn.split(",")
            port_names[i] = variables[0]
            for j, v in enumerate(variables[1:], 1):
                port_names.insert(i + j, v)

    # TODO currently broken
    # correct port dirs and types list (expand)
    # c = 0
    # for i, (pd, pt) in enumerate(zip(port_dirs, port_types)):
    #     if i in indices:
    #         ii = indices.index(i)
    #         # c += count[ii] - 1
    #         for j in range(1, count[ii]):
    #             port_dirs.insert(i + c, port_dirs[c] + "X")
    #             port_types.insert(i + c, port_types[c])
    #             c += 1

    # names, directions and ports as a list of tuples
    # ports = [(x, y, z) for x, y, z in zip(port_names, port_dirs, port_types)]
    return None


def get_generics(buffer):
    # extract the entity string if it exists
    entity = get_entity(buffer)

    # (                 begin of capture group
    #     generic       "generic"
    #     \s*           zero or more whitespaces
    #     \(            opening parenthesis
    #     .*            any character zero or more times
    #     \)            closing parenthesis
    #     \s*           zero or more whitespaces
    #     ;             semicolon
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # port              "port"
    m = re.search(
        r"(generic\s*\(.*\)\s*;)\s*port", entity, flags=re.IGNORECASE
    )
    if m is None:
        return []
    generic_str = m.group(1)

    # generic variable names
    # (                 begin of capture group----------------------------NAMES
    #     [a-z]         lowercase letter (identifiers must begin with that)
    #     [a-z_0-9]*    lowercase letter/underscore/digit. zero or more times
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # :                 double colon
    # [^=]              any character that is not an equal sign
    generic_names = re.findall(
        r"([a-z][a-z_0-9]*)\s*:[^=]", generic_str, flags=re.IGNORECASE
    )

    # generic variable types
    # :                 double colon
    # \s*               zero or more whitespaces
    # (                 begin of capture group----------------------------TYPES
    #     .*?           any character zero or more times. lazy evaluation
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # :=                double colon and equal sign
    generic_types = re.findall(
        r":\s*(.*?)\s*:=", generic_str, flags=re.IGNORECASE
    )

    # generic variable default values
    # :=                double colon and equal sign
    # \s*               zero or more whitespaces
    # (                 begin of capture group-------------------DEFAULT VALUES
    #     .*?           any character zero or more times. lazy evaluation
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # (?:               begin of non-capture group
    #     ;             semicolon
    #     |             OR
    #     (?:           begin of non-capture group
    #         \)        closing parenthesis
    #         \s*       zero or more whitespaces
    #         ;         semicolon
    #     )             end of non-capture group
    # )                 end of non-capture group
    generic_def_vals = re.findall(
        r":=\s*(.*?)\s*(?:;|(?:\)\s*;))", generic_str, flags=re.IGNORECASE
    )

    # names, types and default values as a list of tuples
    generics = [
        (x, y, z)
        for x, y, z in zip(generic_names, generic_types, generic_def_vals)
    ]
    return generics


def get_constants_from_pkg(buffer):
    """
    Gets all constants names from def file specified by function argument
    :param buffer:   str
    :type pkg_file_path:    str
    :return:                a tuple of str lists [name, type, default value] for every constant
    :rtype:                 TODO
    """
    buffer = _get_raw_vhdl(buffer)

    # constant          "constant"
    # \s+               one or more whitespaces
    # (                 begin of capture group
    #     [a-z]         identifiers must begin with a letter
    #     [a-z_0-9]*    any letter, underscore or digit. zero or more times
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # :                 double colon
    names = re.findall(
        r"constant\s+([a-z][a-z_0-9]*)\s*:", buffer, flags=re.IGNORECASE,
    )

    # TODO evaluate if this is needed
    # # type              "type"
    # # \s+               one or more whitespaces
    # # [a-z]             identifiers must begin with a letter
    # # [a-z_0-9]*        any letter, underscore or digit. zero or more times
    # # \s+               one or more whitespaces
    # # is                "is"
    # # \s*               zero or more whitespaces
    # # \(                opening parenthesis (escaped)
    # # \s*               zero or more whitespaces
    # # (.[^)]+)          capture group. any char one or more times that's not)
    # # \s*               zero or more whitespaces
    # # \)                closing parenthesis (escaped)
    # # \s*               zero or more whitespaces
    # # ;                 semicolon
    # state_types = re.findall(
    #     r"type\s+([a-z][a-z_0-9]*)\s+is\s*\(\s*(.[^)]+)\s*\)\s*;",
    #     buffer,
    #     flags=re.IGNORECASE,
    # )
    # # [('state_type', 'idle, calculation, finishing ')]
    # #  ^tuple access first element as state_types[0][0]

    # :                 double colon
    # \s*               zero or more whitespaces
    # (                 begin of capture group
    #     .*?           any character zero or more times. lazy evaluation
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # :=                double colon and equals sign
    types = re.findall(r":\s*(.*?)\s*:=", buffer, flags=re.IGNORECASE)

    # :=                double colon and equals sign
    # \s*               zero or more whitespaces
    # (                 begin of capture group
    #     .*?           any character zero or more times. lazy evaluation
    # )                 end of capture group
    # \s*               zero or more whitespaces
    # ;                 semicolon
    def_vals = re.findall(r":=\s*(.*?)\s*;", buffer, flags=re.IGNORECASE)
    return (names, types, def_vals)
