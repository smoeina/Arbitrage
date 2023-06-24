# extract coefficient number(1000) from names like "1000USDT"
def extract_coefficient(name):
    """
    Given a string `name`, this function extracts the starting numeric coefficient 
    from the string and returns it as an integer. If no numeric coefficient is found, 
    the function returns 1. 

    Parameters:
    name (str): The string from which the numeric coefficient is to be extracted.

    Returns:
    int: The integer value of the extracted numeric coefficient or 1 if no numeric 
         coefficient is found.
    """
    coefficient = ""
    for i in name:
        if i.isdigit():
            coefficient += i
        elif coefficient:
            break
    return int(coefficient) if coefficient else 1


print(extract_coefficient("US"))