# 詰将棋検証ソフト　verikichi試作　2026.6.26

import pickle
import sys
import os

import tsume_solver2mdsc
from tsume_solver2mdsc import Shogi_Operation
from gonkichi_app import TsumeShogi
from MyUtils import StopWatch

import shogi as pth
from shogi import Shogi

from MyUtils import StopWatch

# INPUTパラメータ　↓検証したい詰将棋をpickleに保存して、パス・ファイル名・検証深さを設定してください。
# 少々時間かかります。（参考）オリジナル7手詰めの検証にCython使って6分程度

INPUT_PATH = r"pickle"
INPUT_FILENAME = "オリジナル7手詰め.pickle"
INPUT_VERI_DEPTH = 15


# ★ ここが重要：pickle が参照する __main__.TsumeShogi を登録する
sys.modules['__main__'].TsumeShogi = TsumeShogi

# pickle file読み込み
# folder = r"C:\Users\kawak\dev\shogi\test_pickle"
folder = INPUT_PATH
# filename= "D1_7.pickle"
filename = INPUT_FILENAME

fullpath = os.path.join(folder,filename)

with open (fullpath,'rb') as file:
    tsume = pickle.load(file)
    print(f"loaded file:{fullpath}")


solver = tsume_solver2mdsc.TsumeSolver2mdsc()
solver.progress=False
sw = StopWatch(n_round=3)

shogi = tsume.answer[0]
n_max = tsume.n_tedume
print(shogi)


sw.start()
# ■検証ステップ１：最短手数、回答手順の確認
solver.Solve_IdDfs(shogi,n_max)
answer = solver.GetSolution2()

print("■IDDFS探索結果")
solver.HierPrintDic()

if answer:
    print(f"■Step1:詰み検証\n  最短詰み手数：{len(answer)}\n  正解手順：{answer}")
    print(f" *正解手順数：{len(solver.solutions['answer'])}")
    print(f" *駒余り手順数：{len(solver.solutions['long'])}")
    print(f" *早詰み手順数：{len(solver.solutions['short'])}")
    if answer in solver.solutions['long']:
        print(" ⚠️駒が余ります")
    elif len(solver.solutions['answer']) != 1:
        print(" ⚠️複数の正解手順があります：")
        for proc in solver.solutions['answer']:
            print(f"  手順：{proc}")

sw.lap("Step1")

# ■検証ステップ２：余詰め検証
depth_veri = INPUT_VERI_DEPTH
print(f"■Step2:余詰検証\n  探索深さ：{depth_veri}")

# 再帰メソッドの定義
def verifyYodume(shogi:Shogi,count:int,mainsol,solver:tsume_solver2mdsc.TsumeSolver2mdsc,sw:StopWatch):
    OuteCands = solver.searchOute(shogi)
    rightOute = mainsol[count]

    print(f"rightOute:{rightOute}")
    print(f"OuteCands:{OuteCands}")

    lst_res = []

    for cand in OuteCands:
        if cand == rightOute:
            pass
            # print(f"right:{cand}")
        else:
            # print(f"verify:{str(cand)}  cf {str(rightOute)}")
            solver.dictop = {}
            solver.MapDic = {}
            res = solver_veri.VerifyOuteCand(0,shogi,cand,solver_veri.dictop)
            lst_res.append(res)
            if res:
                sol = [cand] + solver_veri.GetSolution2()
                print(f"⚠️⚠️余詰め発見：{sol}")
            else:
                pass
                # print(f"　↑{solver.MaxStep}手では詰みません")

    print(lst_res)
    if not any(lst_res):
        print(f"  {count+1}手目:検証成功！{solver.MaxStep}手の範囲では、余詰めはありません。")

    sw.lap(f"Step2:{count+1}手目")

    # 次の手を検索
    if count < len(mainsol)-1:
        # 2手進める
        shogi.DoOperation(mainsol[count])
        count += 1
        shogi.DoOperation(mainsol[count])
        count += 1

        verifyYodume(shogi,count,mainsol,solver,sw)

# 余詰め検証メイン処理

solver_veri = tsume_solver2mdsc.TsumeSolver2mdsc()
solver_veri.MaxStep = depth_veri
solver_veri.progress = False

verifyYodume(shogi,0,answer,solver_veri,sw)



sw.show_laps()


