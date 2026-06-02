from pancake import oven


def build():

    # 构建所有服务实例
    for classes in oven.pancake_dough["Service"]:
        oven.pancake_pie["Service"][str(classes)] = oven.pancake_dough["Service"][classes].build()

    for build_method_name in oven.muffin_egg["BuildOrder"]:
        oven.muffin_egg["Builder"][build_method_name[0]]()



