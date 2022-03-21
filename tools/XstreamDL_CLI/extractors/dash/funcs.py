def tree(obj, step: int = 0):
    print(f"{step * '--'}>{obj.name}")
    step += 1
    for child in obj.childs:
        step = tree(child, step=step)
    step -= 1
    print(f"{step * '--'}>{obj.name}")
    return step