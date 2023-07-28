from classv2 import ClassDef, TemplateClassDef
from intbase import InterpreterBase, ErrorType
from bparser import BParser
from objectv2 import ObjectDef
from type_valuev2 import TypeManager

# need to document that each class has at least one method guaranteed

# Main interpreter class
class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output

    # run a program, provided in an array of strings, one string per line of source code
    # usese the provided BParser class found in parser.py to parse the program into lists
    def run(self, program):
        status, parsed_program = BParser.parse(program)
        if not status:
            super().error(
                ErrorType.SYNTAX_ERROR, f"Parse error on program: {parsed_program}"
            )
        self.__add_all_class_types_to_type_manager(parsed_program)
        self.__map_template_class_names_to_template_class_defs(parsed_program)
        self.__map_class_names_to_class_defs(parsed_program)

        # instantiate main class
        invalid_line_num_of_caller = None
        self.main_object = self.instantiate(
            InterpreterBase.MAIN_CLASS_DEF, invalid_line_num_of_caller
        )

        # call main function in main class; return value is ignored from main
        self.main_object.call_method(
            InterpreterBase.MAIN_FUNC_DEF, [], False, invalid_line_num_of_caller
        )

        # program terminates!

    # user passes in the line number of the statement that performed the new command so we can generate an error
    # if the user tries to new an class name that does not exist. This will report the line number of the statement
    # with the new command
    def instantiate(self, class_name, line_num_of_statement):
        if class_name not in self.class_index:
            super().error(
                ErrorType.TYPE_ERROR,
                f"No class named {class_name} found",
                line_num_of_statement,
            )
        class_def = self.class_index[class_name]
        obj = ObjectDef(
            self, class_def, None, self.trace_output
        )  # Create an object based on this class definition
        return obj

    # returns a ClassDef object
    def get_class_def(self, class_name, line_number_of_statement):
        if class_name not in self.class_index:
            super().error(
                ErrorType.TYPE_ERROR,
                f"No class named {class_name} found",
                line_number_of_statement,
            )
        return self.class_index[class_name]

    # returns a bool
    def is_valid_type(self, typename):
        return self.type_manager.is_valid_type(typename)

    # returns a bool
    def is_a_subtype(self, suspected_supertype, suspected_subtype):
        return self.type_manager.is_a_subtype(suspected_supertype, suspected_subtype)

    # typea and typeb are Type objects; returns true if the two type are compatible
    # for assignments typea is the type of the left-hand-side variable, and typeb is the type of the
    # right-hand-side variable, e.g., (set person_obj_ref (new teacher))
    def check_type_compatibility(self, typea, typeb, for_assignment=False):
        return self.type_manager.check_type_compatibility(typea, typeb, for_assignment)

    def __map_class_names_to_class_defs(self, program):
        self.class_index = {}
        for item in program:
            if item[0] == InterpreterBase.CLASS_DEF:
                if item[1] in self.class_index:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Duplicate class name {item[1]}",
                        item[0].line_num,
                    )
                self.class_index[item[1]] = ClassDef(item, self)

    def __map_template_class_names_to_template_class_defs(self, program):
        self.template_class_index = {}
        for item in program:
            if item[0] == InterpreterBase.TEMPLATE_CLASS_DEF:
                if item[1] in self.template_class_index:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Duplicate class name {item[1]}",
                        item[0].line_num,
                    )
                self.template_class_index[item[1]] = TemplateClassDef(item, self)


    # [class classname inherits superclassname [items]]
    def __add_all_class_types_to_type_manager(self, parsed_program):
        self.type_manager = TypeManager()
        for item in parsed_program:
            if item[0] == InterpreterBase.CLASS_DEF:
                class_name = item[1]
                superclass_name = None
                if item[2] == InterpreterBase.INHERITS_DEF:
                    superclass_name = item[3]
                self.type_manager.add_class_type(class_name, superclass_name)


# program_source = [
# '(class main',
#  '(field bool a)',
#  '(method bool foo ()', 
#    '(return true))',
#  '(method void main ()',
#  '(begin',
#   '(print a)',
#   '(set a (call me foo))',
#   '(print a)',
#   ')',
#  ')',
# ')'
# ]

# program_source = [
# '(class main',
#  '(method void foo ((int x))',
#    '(begin', 
#      '(print x)',
#      '(let ((int y))',
#           '(print y)',
#           '(set y 25)',
#           '(print y)',
#      ')',
#    ')',
#  ')',
#  '(method void main ()',
#    '(call me foo 10)',
#  ')',
# ')'
# ]

# program_source = [
# '(class Dog',
# '(field int x 0)',
# ')',

# '(class main',
# '(field Dog e)',
#  '(method void main ()',
#  '(begin',
#  '(set e (new Dog))',
#   '(let ((bool b) (string c) (int d) (Dog e))',
#     '(print b)',  # prints False
#     '(print c)',  # prints empty string
#     '(print d)',  # prints 0
#     '(if (!= e null) (print "value") (print "null"))', # prints null
#   ')',
#  ')',
#  ')',
# ')'
# ]

# program_source = [
# '(class Dog',
# '(field int x 0)',
# ')',

# '(class main',
# '(field main e)',
# '(field int i)',
# '(field bool b)',
# '(field string s)',
#  '(method void main ()',
#  '(begin',
#     '(if (!= e null) (print "value") (print "null"))', # prints null
#     '(print i)',
#     '(print s)',
#     '(print b)',
#  ')',
#  ')',
# ')'
# ]

# program_source = [
# '(tclass MyTemplatedClass (shape_type animal_type)',
#   '(field shape_type some_shape)',
#   '(field animal_type some_animal)',
#   	  '(method void act ((shape_type s) (animal_type a))',
#           '(begin',
#           '(let (MyTemplatedClass@shape_type@animal_type t null))',
#             '(print "Shape area: " (call s get_area))',
#             '(print "Animal name: " (call a get_name))',
#           ')',
#         ')', 
#       ')',

# '(class Square',
#   '(field int side 10)',
#   '(method int get_area () (return (* side side)))',
# ')',

# '(class Dog',
#   '(field string name "koda")',
#   '(method string get_name () (return name))',
# ')',

# '(class main',
#   '(method void main ()',
#     '(let ((Square s) (Dog d) (MyTemplatedClass@Square@Dog t))',
#       '(set s (new Square))',
#       '(set d (new Dog))',
#       '(set t (new MyTemplatedClass@Square@Dog))',
#       '(call t act s d)',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(tclass node (field_type)',
#   '(field node@field_type next null)',
#   '(field field_type value)',
#   '(method void set_val ((field_type v)) (set value v))',
#   '(method field_type get_val () (return value))',
#   '(method void set_next((node@field_type n)) (set next n))',
#   '(method node@field_type get_next() (return next))',
# ')',

# '(class main',
#   '(method void main ()', 
#     '(let ((node@int x null))',
#       '(set x (new node@int))',
#       '(call x set_val 5)',
#       '(print (call x get_val))',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(tclass foo (field_type)',
#   '(method foo@field_type get_me () (return me))',
#   '(method void talk () (print "hi"))',
# ')',

# '(class main',
#   '(method void main ()', 
#     '(let ((foo@int x null))',
#        '(if (== x null) (print "null"))',
#        '(if (== null x) (print "null"))',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(tclass foo (field_type)',
#   '(field field_type value)',
#   '(method void set_val ((field_type v)) (set value v))',
# ')',

# '(class main',
#   '(method void main ()', 
#     '(let ((foo@bool x null))',
#         '(set x (new foo@bool))',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(tclass foo (field_type)',
#   '(method void print ((field_type v)) (print v))',
# ')',

# '(class main',
#   '(method void main ()', 
#     '(let ((foo@int x null) (foo@bool y null))',
#       '(set y (new foo@bool))',
#       '(set x y)',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(tclass Foo (field_type)',
#   '(method void chatter ((field_type x))', 
#     '(call x quack)',         
#   ')',
#   '(method bool compare_to_5 ((field_type x))', 
#     '(return (== x 5))',
#   ')',
# ')',
# '(class Duck',
#  '(method void quack () (print "quack"))',
# ')',

#       '(class main',
#         '(field Foo@Duck t1)',
#         '(field Foo@int t2)',
#         '(method void main ()', 
#           '(begin',
#              '(set t1 (new Foo@Duck))',	# works fine
#              '(set t2 (new Foo@int))',		# works fine

#              '(call t1 chatter (new Duck))',	# works fine - ducks can talk
#              '(call t2 compare_to_5 5)',  	# works fine - ints can be compared
#              '(call t1 chatter 10)',  # generates a NAME ERROR on line A
#           ')',
#         ')',
#       ')'
# ]

# program_source = [
# '(tclass my_generic_class (field_type)',
#   '(method void do_your_thing ((field_type x)) (call x talk))',
# ')',

# '(class duck',
#  '(method void talk () (print "quack"))',
# ')',

# '(class person',
#  '(method void talk () (print "hello"))',
# ')',

# '(class main',
#   '(method void main ()',
#     '(let ((my_generic_class@duck x null)',
#           '(my_generic_class@person y null))',
#       # create a my_generic_class object that works with ducks
#       '(set x (new my_generic_class@duck))',
#       # create a my_generic_class object that works with persons
#       '(set y (new my_generic_class@person))',
#       '(call x do_your_thing (new duck))',
#       '(call y do_your_thing (new person))',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(tclass Foo (field_type)',
#   '(method bool compare_to_5 ((field_type x))', 
#     '(return (== x 5))', #== operator applied to two incompatible types
#   ')',
# ')',

# '(class Duck',
#   '(method void quack ()', 
#     '(print "quack")))',
# '(class main',
#   '(field Foo@Duck t1 null)',
#   '(field Foo@int t2)',
#   '(field Duck d)',
#     '(method void main ()', 
#       '(begin',
#         '(set t1 (new Foo@Duck))',
#         '(set t2 (new Foo@int))',
#         '(call t1 compare_to_5 (new Duck))', #type error generated
# ')))'
# ]

# program_source = [
# '(tclass Foo (field_type)',
#   '(method void chatter ((field_type x))', 
#     '(call x quack)))', #error generated here

# '(class Duck',
#   '(method void quack ()', 
#     '(print "quack")))',
# '(class main',
#   '(field Foo@Duck t1)',
#   '(field Foo@int t2)',
#     '(method void main ()', 
#       '(begin',
#         '(set t1 (new Foo@int))', #changed type of t1
#         '(call t1 chatter 5)', 
# #generates a type error on the line above, mismatch between Foo@Duck and Foo@int
# ')))'
# ]

# program_source = [
# '(class main',
#  '(method void foo ()', 
#    '(throw "blah")',
#  ')',

#  '(method void main ()',
#   '(begin',
#     '(try',
#        '(call me foo)',
#        '(print exception)',
#     ')',
#   ')',
#  ')',
# ')'
# ]

# program_source = [
# '(class main',
#   '(method void bar ()',
#      '(begin',
#         '(print "hi")',
#         '(throw "foo")',
#         '(print "bye")',
#      ')',
#   ')',
#   '(method void main ()',
#     '(begin',
#       '(try',
#        '(call me bar)',
#        '(print "The thrown exception was: " exception)',
#       ')',
#       '(print "done!")',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(class main',
#   '(method void bar ()',
#      '(begin',
#         '(print "hi")',
#         '(throw "foo")',
#         '(print "bye")',
#      ')',
#   ')',
#   '(method void main ()',
#     '(begin',
#       '(try',
#        '(call me bar)',
#        '(print "The thrown exception was: " exception)',
#       ')',
#       '(print "done!" exception)',
#     ')',
#   ')',
# ')'
# ]

# program_source = [
# '(class main',
#  '(method int foo ()', 
#    '(throw "blah")',
#  ')',
#  '(method int bar ((int x))', 
#    '(print x)',
#  ')',

#  '(method void main ()',
#   '(begin',
#     '(try',
#        '(call me bar (call me foo))',
#        '(print exception)',
#     ')',
#   ')',
#  ')',
# ')'
# ]

# program_source = [
# '(class main',
#  '(method void foo ()', 
#    '(throw "blah")',
#  ')',
#  '(method int bar ()', 
#    '(begin',
#     '(try',
#      '(let ((int a 5))',
#        '(call me foo)',
#      ')',
#      '(print exception)',
#     ')', 
#     '(print a)', # fails
#    ')',
#  ')',

#  '(method void main ()',
#     '(call me bar)',
#  ')',
# ')'
# ]

# test = Interpreter(console_output=True, inp=None, trace_output=False)
# test.run(program_source)