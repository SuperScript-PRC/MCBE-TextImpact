from mctext.align import cut_by_length, align_simple, get_line_width
from mctext.render import render
from mctext.pad import pad_with_format

# render(
#     "font_images",
#     align_simple("你好", 20, "我们正在制表", 20, "这是表单内容", 20, "请观看！")
#     + "\n"
#     + align_simple("Happy2018New", 20, "0o000", 20, "高兴", 20, "Owner")
#     + "\n"
#     + align_simple("2401PT", 20, "0o001", 20, "7**3", 20, "Admin")
#     + "\n"
#     + align_simple("SuperScript", 20, "0o002", 20, "超级脚本", 20, "这是？"),
# ).save("simulate.png")

# length1 = render("font_images", "Happy  1983  New").width
# length2 = get_line_width("Happy  1983  New")

# print(length1, length2)

orig=\
    "§b头盔(pad1)|§r陨铁头盔(pad2)|§6陨铁套装 §e二件套(pad3)|§a生命值低于35%时(pad4)| \n"+\
    "§7胸甲(pad1)|§r陨铁护甲(pad2)|§6陨铁套装 §e四件套(pad3)|§a无(pad4)|最右一格\n"+\
    " (pad1)|可以占多个格子,这是两个(pad3)|\n"+\
    " (pad1)|可以占多个格子,这是三个也OK(pad4)|\n"+\
    "跨行(pad1)|对齐(pad2)|也不是(pad3)|问题\n"+\
    "不那么规矩，(pad3)|也没问题呢(pad4)|～"
# lines=orig.split("\n")
# line_frags=[l.split("(pad)") for l in lines]
# frags_count=len(line_frags[0])
# assert all([len(frags)==frags_count for frags in line_frags])
# out_texts=[""for _ in range(frags_count)]
# for f_i in range(frags_count):
#     input_texts=[
#         c+i for c,i in zip(out_texts,[lf[f_i] for lf in line_frags])
#     ]
#     if f_i !=frags_count-1:
#         out_texts=pad(input_texts)
#     else:
#         out_texts=input_texts
padded=pad_with_format(orig)
print(padded)
render("font_png",padded).save("simulate.png")