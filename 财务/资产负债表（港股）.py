# -*- encoding:utf-8 -*-

# Date: 2025/8/22
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import traceback

pd.set_option('display.max_columns', None)  # 显示所有列
pd.set_option('display.max_rows', None)
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def convert_chinese_number(value, to_unit='亿'):
    """
    将中文数字字符串转换为指定单位的浮点数
    例如: "7734.47万" -> 0.773447 (转换为亿)
    """
    if pd.isna(value) or value == 'False' or value == False:
        return 0.0

    # 处理字符串类型的值
    if isinstance(value, str):
        # 提取数字部分和单位
        match = re.search(r'([\d\.]+)([亿万]*)', value)
        if match:
            number = float(match.group(1))
            unit = match.group(2)

            if unit == '亿':
                return number  # 已经是亿单位
            elif unit == '万':
                return number / 10000  # 万转换为亿
            else:
                return number / 100000000  # 假设是元，转换为亿
    elif isinstance(value, (int, float)):
        return value / 100000000  # 假设是元，转换为亿

    return 0.0


def get_item_value(df, item_code, default=0.0):
    """
    安全获取财务项目值
    """
    try:
        filtered = df[df['STD_ITEM_CODE'] == item_code]
        if not filtered.empty:
            return filtered['AMOUNT'].values[0]
        return default
    except Exception:
        return default


def create_balance_sheet_chart(stock_code):
    """
    创建资产负债表可视化图表（所有项目在同一坐标系中，单位：亿）
    """
    try:
        # 获取财务数据
        df = ak.stock_financial_hk_report_em(stock_code, indicator='报告期')

        if df.empty:
            print(f"无法获取股票代码 {stock_code} 的财务数据")
            return

        # 获取最新的报告期数据
        latest_report = df
        report_date = latest_report['FISCAL_YEAR'].iloc[0]
        st_name = latest_report["SECURITY_NAME_ABBR"].iloc[
            0] if "SECURITY_NAME_ABBR" in latest_report.columns else stock_code

        # 获取市值数据
        try:
            dhk_spot_em_df = ak.stock_hk_valuation_baidu(symbol=stock_code)
            if not dhk_spot_em_df.empty:
                new_price = dhk_spot_em_df.iloc[-1].value
            else:
                new_price = 0
        except Exception:
            new_price = 0
            print("警告: 无法获取市值数据")

        # 提取关键数据并转换为亿单位
        data = {
            '总市值': new_price,
            # 资产项目
            '现金及等价物': convert_chinese_number(get_item_value(latest_report, '004002010'), '亿'),
            '短期存款': convert_chinese_number(get_item_value(latest_report, '004002011'), '亿'),
            '中长期存款': convert_chinese_number(get_item_value(latest_report, '004001030'), '亿'),
            '受限制存款及现金': convert_chinese_number(get_item_value(latest_report, '004002009'), '亿'),
            '应收帐款': convert_chinese_number(get_item_value(latest_report, '004002003'), '亿'),
            '存货': convert_chinese_number(get_item_value(latest_report, '004002001'), '亿'),
            '其他应收款': convert_chinese_number(get_item_value(latest_report, '004002005'), '亿'),
            '固定资产': convert_chinese_number(get_item_value(latest_report, '004001002'), '亿'),
            '无形资产': convert_chinese_number(get_item_value(latest_report, '004001004'), '亿'),
            '投资性房地产': convert_chinese_number(get_item_value(latest_report, '004001003'), '亿'),
            '非流动资产合计': convert_chinese_number(get_item_value(latest_report, '004001999'), '亿'),
            '流动资产合计': convert_chinese_number(get_item_value(latest_report, '004002999'), '亿'),
            '总资产': convert_chinese_number(get_item_value(latest_report, '004009999'), '亿'),

            # 负债和权益项目
            '短期借款': convert_chinese_number(get_item_value(latest_report, '004011010'), '亿'),
            '应付帐款': convert_chinese_number(get_item_value(latest_report, '004011001'), '亿'),
            '其他应付款': convert_chinese_number(get_item_value(latest_report, '004011008'), '亿'),
            '应付税项': convert_chinese_number(get_item_value(latest_report, '004011003'), '亿'),
            '流动负债合计': convert_chinese_number(get_item_value(latest_report, '004011999'), '亿'),
            '长期借款': convert_chinese_number(get_item_value(latest_report, '004020005'), '亿'),
            '非流动负债合计': convert_chinese_number(get_item_value(latest_report, '004020999'), '亿'),
            '总负债': convert_chinese_number(get_item_value(latest_report, '004025999'), '亿'),
            '股东权益': convert_chinese_number(get_item_value(latest_report, '004030999'), '亿'),
        }

        # 创建图表
        fig, ax = plt.subplots(figsize=(16, 10))

        # 设置标题
        plt.title(f'{st_name}({stock_code}) 资产负债表 - {report_date}', fontsize=16, fontweight='bold')

        sz_items = ["总市值"]
        sz_values = [data[item] for item in sz_items]

        # 资产项目
        asset_items = [
            '现金及等价物', '短期存款', '中长期存款', '受限制存款及现金', '应收帐款', '存货', '其他应收款',
            '固定资产', '无形资产', '投资性房地产',
            '流动资产合计', '非流动资产合计', '总资产'
        ]
        asset_values = [data[item] for item in asset_items]

        # 负债和权益项目
        liability_items = [
            '短期借款', '应付帐款', '其他应付款', '应付税项',
            '流动负债合计', '长期借款', '非流动负债合计', '总负债'
        ]
        liability_values = [data[item] for item in liability_items]

        # 所有者权益项目
        equity_items = ['股东权益']
        equity_values = [data[item] for item in equity_items]

        # 所有项目合并
        all_items = sz_items + asset_items + liability_items + equity_items
        all_values = sz_values + asset_values + liability_values + equity_values

        # 颜色设置
        colors = []
        for item in all_items:
            if item in asset_items:
                colors.append('#1f77b4')  # 蓝色 - 资产
            elif item in sz_items:
                colors.append('#D4AF37')  # 金色 - 市值
            elif item in liability_items:
                colors.append('#d62728')  # 红色 - 负债
            else:
                colors.append('#2ca02c')  # 绿色 - 权益

        # 绘制柱状图（所有项目在同一坐标系中）
        x_pos = np.arange(len(all_items))
        bars = ax.bar(x_pos, all_values, color=colors, alpha=0.7)

        # 设置X轴标签
        ax.set_xticks(x_pos)
        ax.set_xticklabels(all_items, rotation=45, ha='right')
        ax.set_ylabel('金额 (亿)')

        # 添加数值标签
        max_value = max(all_values) if all_values else 1
        for i, v in enumerate(all_values):
            ax.text(i, v + max_value * 0.01, f'{v:.2f}亿', ha='center', fontweight='bold')

        # 添加分隔线
        if all_items:
            ax.axvline(x=len(sz_items) - 0.5, color='black', linestyle='--', alpha=0.5)
            ax.axvline(x=len(sz_items) + len(asset_items) - 0.5, color='black', linestyle='--', alpha=0.5)
            ax.axvline(x=len(sz_items) + len(asset_items) + len(liability_items) - 0.5,
                       color='black', linestyle='--', alpha=0.5)

        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#D4AF37', label='市值'),
            Patch(facecolor='#1f77b4', label='资产项目'),
            Patch(facecolor='#d62728', label='负债项目'),
            Patch(facecolor='#2ca02c', label='权益项目')
        ]
        ax.legend(handles=legend_elements, loc='upper right')

        # 添加网格
        ax.grid(True, axis='y', alpha=0.3)

        # 调整布局
        plt.tight_layout()

        # 显示图表
        plt.show()

        # 打印详细数据
        print("=" * 60)
        print(f"{stock_code} 资产负债表详细数据 - {report_date}")
        print("=" * 60)

        print("\n资产项目:")
        for item in asset_items:
            print(f"  {item}: {data[item]:.2f}亿")

        print("\n负债项目:")
        for item in liability_items:
            print(f"  {item}: {data[item]:.2f}亿")

        print("\n权益项目:")
        for item in equity_items:
            print(f"  {item}: {data[item]:.2f}亿")

        total_assets = data['总资产']
        total_liab = data['总负债']
        total_equity = data['股东权益']

        print(f"\n资产总计: {total_assets:.2f}亿")
        print(f"负债总计: {total_liab:.2f}亿")
        print(f"权益总计: {total_equity:.2f}亿")
        print(f"负债和权益总计: {total_liab + total_equity:.2f}亿")

        # 检查资产负债表是否平衡
        if abs(total_assets - (total_liab + total_equity)) > 0.01:
            print(f"注意: 资产负债表不平衡，差异: {abs(total_assets - (total_liab + total_equity)):.2f}亿")

        # 计算市净率
        if total_equity > 0:
            pb_ratio = data['总市值'] / total_equity
            print(f"\n市净率 (PB): {pb_ratio:.2f}")
        else:
            print("\n无法计算市净率，股东权益为零")

    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        traceback.print_exc()
        print("可用的数据列:")
        if 'df' in locals() and not df.empty:
            print(df.columns)
            print("\n可用的项目代码和名称:")
            print(df[['STD_ITEM_CODE', 'STD_ITEM_NAME']].drop_duplicates())


def main(stock):
    create_balance_sheet_chart(stock)


if __name__ == '__main__':
    main("00716")
