import benchmark_my_code

def sum_of_digits_using_string(number):
    return sum(int(digit) for digit in str(number))

def sum_of_digits_using_modulo(number):
    sum = 0
    while number > 0:
        sum += number % 10
        number //= 10
    return sum


variants = (1, 10, 123, 4567, 89012, 345678, 67890123, 456789012, 1234567890)

benchmark_my_code.bench(sum_of_digits_using_modulo, variants)
benchmark_my_code.bench(sum_of_digits_using_string, variants)