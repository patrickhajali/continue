
def is_even_length(lst) -> bool:
   return len(lst) % 2 == 0

def is_empty(lst):
   return len(lst) == 0

def product_of_elements(iterable):
    if len(iterable) == 0:
        return 0
    total = 1
    for item in iterable:
        total *= item
    return total

def remove_binary_prefix(bin_str):
    if bin_str[:2] == '0b':
        return bin_str[2:]
    else:
        return bin_str

def remove_duplicates(iterable):
    return list(set(iterable))

def get_even_numbers(iterable):
    return [i for i in iterable if i % 2 == 0]

def get_odd_numbers(iterable):
    return [i for i in iterable if i % 2 != 0]

def are_same_length(list1, list2):
   return len(list1) == len(list2)
