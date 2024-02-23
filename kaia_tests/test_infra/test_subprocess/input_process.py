if __name__ == '__main__':
    s = input()
    if s=='err':
        raise ValueError("Error5432")
    else:
        print("input was "+s, end='')