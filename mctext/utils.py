import math


def approximate_sum_optimized(A: int, B: int, C: int) -> tuple[int, int, int]:
    """
    优化版本：使用数学方法减少搜索空间

    Args:
        A: 第一个数
        B: 第二个数
        C: 目标值

    Returns:
        tuple: (x, y, diff) 其中 x*A + y*B ≈ C, diff为差值
    """
    if A == 0 and B == 0:
        return (0, 0, abs(C))

    best_x, best_y = 0, 0
    best_diff = abs(C)

    # 如果其中一个数为0，直接计算
    if A == 0:
        if B != 0:
            y = round(C / B)
            return (0, y, abs(y * B - C))
    elif B == 0:
        x = round(C / A)
        return (x, 0, abs(x * A - C))

    # 计算搜索范围
    max_range = max(
        abs(C // A) + 1 if A != 0 else 0, abs(C // B) + 1 if B != 0 else 0, 100
    )

    # 遍历x的可能值，并计算最优的y
    for x in range(-max_range, max_range + 1):
        # 对于固定的x，计算最优的y
        if B != 0:
            # 理想的y值
            ideal_y = (C - x * A) / B
            # 检查理想y附近的整数值
            for y in [int(ideal_y), int(ideal_y) + 1, int(ideal_y) - 1]:
                sum_val = x * A + y * B
                diff = abs(sum_val - C)

                if diff < best_diff:
                    best_diff = diff
                    best_x, best_y = x, y

                if diff == 0:
                    return best_x, best_y, best_diff
        else:
            # B为0的情况
            sum_val = x * A
            diff = abs(sum_val - C)

            if diff < best_diff:
                best_diff = diff
                best_x, best_y = x, 0

            if diff == 0:
                return best_x, best_y, best_diff

    return best_x, best_y, best_diff


def find_closest(a: int, b: int, c: int):
    if a <= 0 or b <= 0:
        raise ValueError("a和b必须大于0")
    min_diff = float("inf")  # 初始化最小差值为无穷大
    final_diff = min_diff
    solutions = []  # 存储所有最优解

    # 确定x的遍历范围，确保覆盖足够多的可能值
    max_ab = max(a, b)
    x_max = int((c + max_ab) / a) + 2  # 上限计算，避免遗漏

    x = 1
    while x <= x_max:
        x_a = x * a  # 当前x对应的a的总和
        y_ideal = (c - x_a) / b  # 理想的y值（可能非整数）

        # 生成y的候选值（围绕理想值，确保y为正整数）
        y_floor = max(0, math.floor(y_ideal))
        y_ceil = max(0, math.ceil(y_ideal))
        y_round = max(0, round(y_ideal))
        y_candidates = {0, y_floor, y_ceil, y_round}  # 去重

        # 检查每个候选y
        for y in y_candidates:
            total = x_a + y * b  # 总和
            current_diff = abs(total - c)  # 与c的差值

            # 更新最小差值和最优解
            if current_diff < min_diff:
                min_diff = current_diff
                final_diff = total - c
                solutions = [(x, y, total)]
            elif current_diff == min_diff:
                solutions.append((x, y, total))

        x += 1

    return solutions, final_diff

