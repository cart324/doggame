import os

with open("card.txt", "r", encoding="UTF-8") as file:
    card_list = file.readlines()
    is_passed = True
    line_count = 1

    for i in card_list:
        if "_" not in i or i.count("_") > 3:
            is_passed = False
            print("line : ", line_count)
        else:
            pass
        line_count += 1
    
    if is_passed:
        print("이상이 없습니다.")

os.system("pause")
