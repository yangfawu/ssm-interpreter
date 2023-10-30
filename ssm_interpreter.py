import sys
from typing import List, Generator, Tuple

class Token:
    def __init__(self, val: str, line: int):
        self.val = val
        self.line = line
    
    def __repr__(self):
        return f"Token(w={self.val}, line={self.line+1})"

class ExpectedNonLabel(Exception):
    def __init__(self, token: "Token"):
        super().__init__(f"Expected a non-label, but got {token}")

class DuplicateLabel(Exception):
    def __init__(self, token: "Token"):
        super().__init__(f"Got {token} as a label, but already saw it")

class UnknownInstruction(Exception):
    def __init__(self, name: str):
        super().__init__(name)

class UnknownLabel(Exception):
    def __init__(self, name: str):
        super().__init__(name) 

class MissingArguments(Exception):
    pass

class EmptyStack(Exception):
    pass

class InvalidProgramUsage(Exception):
    pass

class MissingLabel(Exception):
    def __init__(self, line: int):
        super().__init__(f"Expected label at line {line+1}, but got empty string") 

class LabelInfiniteLoop(Exception):
    def __init__(self, label: str):
        super().__init__(f"Will definitely occur by running instructions after [{label=}]")

class InvalidInteger(Exception):
    def __init__(self, token: "Token"):
        super().__init__(f"Expected an integer, but got {token}")

class DanglingLabel(Exception):
    def __init__(self, label: str):
        super().__init__(f"Expected an instruction after [{label=}]")

####################################

class Node:
    def __init__(self, val: int, next: "Node" = None):
        self.val = val
        self.next = next

class Stack:
    def __init__(self):
        self.top = None
        self.size = 0
    
    def push(self, val: int):
        self.top = Node(val, self.top)
        self.size+= 1
    
    def pop(self) -> int:
        if self.top == None:
            raise EmptyStack()
        out, self.top = self.top, self.top.next
        return out.val
    
    def peek(self) -> int:
        if self.top == None:
            raise EmptyStack()
        return self.top.val
    
    def __repr__(self):
        out = []
        top = self.top
        while top != None:
            out.append(top.val)
            top = top.next
        return repr(out)

####################################

class Operator:
    def __init__(self, args_needed: int = 0):
        self.args_needed = args_needed
    
    def process_args(self, args: Tuple["Token", ...]):
        """
        you can modify the args here
        you can work with the confidence that the number of arguments is exactly how many you uneed
        """
        pass

    def validate_args(self, args: Tuple["Token", ...], driver: "Driver"):
        """
        this is where you can run further checks on the arguments after all instructions have been registered
        """
        pass
    
    def execute(self, args: Tuple["Token", ...], driver: "Driver") -> bool:
        """
        return True if you want to go to next line
        return False if you don't want to go to next line (maybe because you are jumping)
        """
        return True 

class Driver:
    def __init__(self):
        self.stack = Stack()
        self.store = {}
        self.operators = {}

        self.instructions = []
        self.label_map = {}

        self.next_instruction_index = 0
    
    def register_op(self, name: str, op: "Operator"):
        self.operators[name] = op
    
    def get_op(self, name: str) -> "Operator":
        try:
            return self.operators[name]
        except KeyError:
            raise UnknownInstruction(name)
    
    def has_label(self, label: str) -> bool:
        return label in self.label_map
    
    def jump_to_label(self, label: str):
        self.next_instruction_index = self.label_map[label]

    def add_instruction(self, op: "Operator", args: Tuple["Token", ...], label: str = None):
        if label != None:
            self.label_map[label] = len(self.instructions)
        op.process_args(args)
        self.instructions.append((op, args))
    
    def validate_all_instructions(self):
        for op, args in self.instructions:
            op.validate_args(args, self)

    def step(self) -> bool:
        # return False to stop stepping
        if self.next_instruction_index >= len(self.instructions):
            return False

        # run instruction to determine next step
        op, args = self.instructions[self.next_instruction_index]
        if op.execute(args, self):
            self.next_instruction_index+= 1

        # return True to go to next step
        return True

class SSM_ildc(Operator):
    """
    ildc [imm]
        push [imm] into stack
    """

    def __init__(self):
        super().__init__(1)

    def process_args(self, args):
        token = args[0]
        try:
            token.val = int(token.val)
        except ValueError:
            raise InvalidInteger(token)
    
    def execute(self, args, driver):
        driver.stack.push(args[0].val)
        return True

class SSM_iadd(Operator):
    """
    iadd
        replace top 2 numbers of stack with (top1 + top2)
    """
    
    def execute(self, _, driver):
        a = driver.stack.pop()
        b = driver.stack.pop()
        driver.stack.push(a + b)
        return True

class SSM_isub(Operator):
    """
    isub
        replace top 2 numbers of stack with (top2 - top1)
    """
    
    def execute(self, _, driver):
        a = driver.stack.pop()
        b = driver.stack.pop()
        driver.stack.push(b - a)
        return True

class SSM_imul(Operator):
    """
    imul
        replace top 2 numbers of stack with (top1 * top2)
    """
    
    def execute(self, _, driver):
        a = driver.stack.pop()
        b = driver.stack.pop()
        driver.stack.push(a * b)
        return True

class SSM_idiv(Operator):
    """
    idiv
        replace top 2 numbers of stack with (top2 // top1)
    """
    
    def execute(self, _, driver):
        a = driver.stack.pop()
        b = driver.stack.pop()
        driver.stack.push(b // a)
        return True

class SSM_imod(Operator):
    """
    imod
        same as idiv, but you get remainder
    """
    
    def execute(self, _, driver):
        a = driver.stack.pop()
        b = driver.stack.pop()
        driver.stack.push(b % a)
        return True

class SSM_pop(Operator):
    """
    pop
        remove topmost number from stack
    """
    
    def execute(self, _, driver):
        driver.stack.pop()
        return True

class SSM_dup(Operator):
    """
    dup
        duplicate topmost number of the stack
    """

    def execute(self, _, driver):
        a = driver.stack.peek()
        driver.stack.push(a)
        return True

class SSM_swap(Operator):
    """
    swap
        swap positions of the top 2 numbers of the stack
    """
    
    def execute(self, _, driver):
        a = driver.stack.pop()
        b = driver.stack.pop()
        driver.stack.push(a)
        driver.stack.push(b)
        return True

class SSM__base_jump(Operator):
    def __init__(self):
        super().__init__(1)
    
    def validate_args(self, args, driver):
        label = args[0].val
        if not driver.has_label(label):
            raise UnknownLabel(label)

class SSM_jz(SSM__base_jump):
    """
    jz [label]
        remove top element from stack
        if element is 0, jump to label
        if element is not, then go to next
    """
    
    def execute(self, args, driver):
        a = driver.stack.pop()
        if a == 0:
            driver.jump_to_label(args[0].val)
            return False
        return True

class SSM_jnz(SSM__base_jump):
    """
    jnz [label]
        opposite of jz
    """
    
    def execute(self, args, driver):
        a = driver.stack.pop()
        if a != 0:
            driver.jump_to_label(args[0].val)
            return False
        return True

class SSM_jmp(SSM__base_jump):
    """
    jmp [label]
        jump to label
    """

    def __init__(self):
        super().__init__()
        self._memo = {}
    
    def _check_for_definite_infinite_loop(self, label: str, driver: "Driver") -> bool:
        """
        we can have many jmp instructions that jump to the same label
        we can just check if the label causes a definite infinite loop once 
        and cache the result for future checks

        this causes the program check to perform worse than O(n)
        but this will try to minimize the cost of the checks as much as possible
        """
        if label in self._memo:
            return self._memo[label]

        starting_instruction_idx = driver.label_map[label]
        for i in range(starting_instruction_idx, len(driver.instructions)):
            op, ins_args = driver.instructions[i]
            if isinstance(op, SSM__base_jump):
                if isinstance(op, SSM_jmp):
                    if ins_args[0].val == label:
                        self._memo[label] = True
                        return True
                    break
                break
        
        self._memo[label]  = False
        return False

    def validate_args(self, args, driver):
        super().validate_args(args, driver)
        
        label = args[0].val
        if self._check_for_definite_infinite_loop(label, driver):
            raise LabelInfiniteLoop(label)

    def execute(self, args, driver):
        driver.jump_to_label(args[0].val)
        return False

class SSM_load(Operator):
    """
    load
        remove topmost number from stack
        uses number as a key to lookup value on the store
        pushes the value onto the stack
    """

    def execute(self, _, driver):
        key = driver.stack.pop()
        value = driver.store[key]
        driver.stack.push(value)
        return True

class SSM_store(Operator):
    """
    store 
        remove the topmost 2 numbers from the stack
        use top2 as the key
        use top1 as the value
        put key and value onto store
    """
    
    def execute(self, _, driver):
        value = driver.stack.pop()
        key = driver.stack.pop()
        driver.stack[key] = value
        return True

####################################

TokenGenerator = Generator[Tuple["Token", bool], None, None]

class Scanner:
    def __init__(self, filename: str):
        self._gen = self.__create_generator(filename)
    
    def __create_generator(self, filename: str) -> TokenGenerator:
        """
        reads in a file and creates a generator
        the generator outputs a (Token, is token a label?) every time
        """
        with open(filename, "r") as file:
            for i, raw_line in enumerate(file):
                seen_comment = False
                for w in raw_line.split():
                    # once we see a comment, we cannot use the rest of the words
                    if seen_comment:
                        continue
                    
                    # handle comments
                    hashtag_i = w.find("#")
                    if hashtag_i >= 0:
                        seen_comment = True

                        # if the # appears after characters, we send the token out
                        if hashtag_i > 0:
                            w = w[:hashtag_i]
                        else:
                            continue
                    
                    # handle potentially continuous labels
                    while len(w) > 0:
                        colon_i = w.find(":")
                        if colon_i >= 0:
                            prefix, w = w.split(":", 1)

                            # if the colon is the first character, there is no label
                            if colon_i == 0:
                                raise MissingLabel(i)
                            
                            # else the prefix before the colon is a label
                            yield (Token(prefix, i), True)
                        else:
                            yield (Token(w, i), False)
                            break

    def next_token(self) -> Tuple["Token", bool]:
        return next(self._gen)
    
    def next_args(self, n: int) -> Tuple["Token", ...]:
        args = []
        for _ in range(n):
            token, is_label = next(self._gen)
            if is_label:
                raise ExpectedNonLabel(token)
            args.append(token)
        return tuple(args)

####################################

def main():
    if len(sys.argv) != 2:
        raise InvalidProgramUsage()
    
    # create driver and register known instructions
    driver = Driver()
    driver.register_op("ildc", SSM_ildc())
    driver.register_op("iadd", SSM_iadd())
    driver.register_op("isub", SSM_isub())
    driver.register_op("imul", SSM_imul())
    driver.register_op("idiv", SSM_idiv())
    driver.register_op("imod", SSM_imod())
    driver.register_op("pop", SSM_pop())
    driver.register_op("dup", SSM_dup())
    driver.register_op("swap", SSM_swap())
    driver.register_op("jz", SSM_jz())
    driver.register_op("jnz", SSM_jnz())
    driver.register_op("jmp", SSM_jmp())
    driver.register_op("load", SSM_load())
    driver.register_op("store", SSM_store())

    # read input file and parse instructions
    scanner = Scanner(sys.argv[1])
    unregistered_label = None
    while True:
        need_args = False
        try:
            token, is_label = scanner.next_token()
            if is_label:
                # if we already have a label to deal with, we cannot handle the current one
                if unregistered_label != None:
                    raise ExpectedNonLabel(token)

                label = token.val
                if driver.has_label(label):
                    raise DuplicateLabel(token)

                unregistered_label = label
            else:
                op = driver.get_op(token.val)

                # use a boolean lock in case anything goes wrong
                need_args = True
                args = scanner.next_args(op.args_needed)
                need_args = False

                # add instruction with label if any
                driver.add_instruction(op, args, unregistered_label)
                unregistered_label = None
        except StopIteration:
            # there are no more stuff to read

            if need_args:
                raise MissingArguments()
            
            # if we dont need anything else, move onto validating
            break
    
    if unregistered_label != None:
        raise DanglingLabel(unregistered_label)
    
    # after we passed through all instructions, we need to verify that things like labels work out
    driver.validate_all_instructions()

    # program execution
    while True:
        if not driver.step():
            break
        # print(driver.stack)
    
    # print the result
    print(driver.stack.pop())

if __name__ == "__main__":
    main()
