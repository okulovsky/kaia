if __name__ == '__main__':
    with open('/resources/input','r') as input:
        data = input.read()
    for i in range(100):
        print(f'{i}%')
    with open('/resources/output', 'w') as output:
        output.write('output '+data)