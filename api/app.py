from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os
import random
import logging
from datetime import datetime

# 修改日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()  # 只使用控制台输出
    ]
)
logger = logging.getLogger(__name__)

# 获取当前文件所在目录的上级目录路径
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 确保static目录存在
static_dir = os.path.join(base_dir, 'static')
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    if not os.path.exists(os.path.join(static_dir, 'images')):
        os.makedirs(os.path.join(static_dir, 'images'))
    if not os.path.exists(os.path.join(static_dir, 'sounds')):
        os.makedirs(os.path.join(static_dir, 'sounds'))

# 初始化Flask应用，设置模板和静态文件目录
app = Flask(__name__, 
           template_folder=os.path.join(base_dir, 'templates'),
           static_folder=os.path.join(base_dir, 'static'),
           static_url_path='/static')

# 游戏状态
BOARD_SIZE = 15
game_state = {
    'board': [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)],
    'current_player': 'black',
    'ai_enabled': True,  # 新增AI开关
    'game_over': False,  # 新增游戏结束标志
    'winner': None,      # 新增获胜者标志
    'last_move': None,   # 新增最后一步位置
    'move_history': []   # 新增移动历史记录
}

# 方向向量
DIRECTIONS = [(1,0), (0,1), (1,1), (1,-1)]

# 棋型分数定义
SCORES = {
    'win5': 100000,    # 连五
    'alive4': 10000,   # 活四
    'double_dead4': 10000,  # 双冲四
    'dead4_alive3': 8000,   # 冲四活三
    'alive3': 5000,    # 活三
    'double_alive3': 8000,  # 双活三
    'dead4': 1000,     # 冲四
    'dead3': 500,      # 眠三
    'alive2': 400,     # 活二
    'dead2': 100,      # 眠二
    'alive1': 50,      # 活一
    'block5': 100000,  # 防守连五
    'block4': 10000,   # 防守活四
    'block3': 5000     # 防守活三
}

def evaluate_position(row, col, player, depth=0):
    """评估某个位置的分数"""
    if game_state['board'][row][col] is not None:
        return -1
        
    board = game_state['board']
    opponent = 'black' if player == 'white' else 'white'
    
    def count_consecutive(x, y, dx, dy, player):
        """计算某个方向上的连续棋子数和两端空位数"""
        count = 1  # 当前位置算一个
        space_before = 0  # 前端空位
        space_after = 0   # 后端空位
        block_before = False  # 前端是否被对手堵住
        block_after = False   # 后端是否被对手堵住
        
        # 向后检查
        tx, ty = x + dx, y + dy
        while 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
            if board[tx][ty] == player:
                count += 1
            elif board[tx][ty] is None:
                space_after += 1
                break
            else:
                block_after = True
                break
            tx += dx
            ty += dy
            
        # 向前检查
        tx, ty = x - dx, y - dy
        while 0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE:
            if board[tx][ty] == player:
                count += 1
            elif board[tx][ty] is None:
                space_before += 1
                break
            else:
                block_before = True
                break
            tx -= dx
            ty -= dy
            
        return count, space_before, space_after, block_before, block_after
    
    def check_pattern(x, y, player):
        """检查所有方向的棋型"""
        patterns = {
            'win5': 0,
            'alive4': 0,
            'dead4': 0,
            'alive3': 0,
            'dead3': 0,
            'alive2': 0,
            'dead2': 0,
            'alive1': 0
        }
        
        # 模拟在此位置下棋
        board[x][y] = player
        
        for dx, dy in DIRECTIONS:
            count, space_before, space_after, block_before, block_after = count_consecutive(x, y, dx, dy, player)
            
            # 连五
            if count >= 5:
                patterns['win5'] += 1
                continue
                
            # 活四
            if count == 4 and space_before and space_after:
                patterns['alive4'] += 1
            # 冲四
            elif count == 4 and (space_before or space_after):
                patterns['dead4'] += 1
            # 活三
            elif count == 3 and space_before and space_after and not (block_before or block_after):
                patterns['alive3'] += 1
            # 眠三
            elif count == 3 and (space_before or space_after):
                patterns['dead3'] += 1
            # 活二
            elif count == 2 and space_before and space_after and not (block_before or block_after):
                patterns['alive2'] += 1
            # 眠二
            elif count == 2 and (space_before or space_after):
                patterns['dead2'] += 1
            # 活一
            elif count == 1 and space_before and space_after and not (block_before or block_after):
                patterns['alive1'] += 1
        
        # 撤销模拟
        board[x][y] = None
        
        return patterns
    
    # 评估当前位置
    score = 0
    my_patterns = check_pattern(row, col, player)
    opp_patterns = check_pattern(row, col, opponent)
    
    # 必胜点
    if my_patterns['win5']:
        return SCORES['win5']
    
    # 必防点
    if opp_patterns['win5']:
        return SCORES['win5'] * 0.9
    
    # 计算进攻分数
    if my_patterns['alive4'] or my_patterns['dead4'] >= 2:
        score += SCORES['alive4']
    elif my_patterns['dead4'] and my_patterns['alive3']:
        score += SCORES['dead4_alive3']
    elif my_patterns['alive3'] >= 2:
        score += SCORES['double_alive3']
    else:
        score += (my_patterns['alive4'] * SCORES['alive4'] +
                 my_patterns['dead4'] * SCORES['dead4'] +
                 my_patterns['alive3'] * SCORES['alive3'] +
                 my_patterns['dead3'] * SCORES['dead3'] +
                 my_patterns['alive2'] * SCORES['alive2'] +
                 my_patterns['dead2'] * SCORES['dead2'] +
                 my_patterns['alive1'] * SCORES['alive1'])
    
    # 计算防守分数（根据对手棋型）
    defense_score = 0
    if opp_patterns['win5']:
        defense_score += SCORES['block5']  # 必须防守连五
    elif opp_patterns['alive4']:
        defense_score += SCORES['block4']  # 必须防守活四
    elif opp_patterns['dead4'] >= 2:
        defense_score += SCORES['double_dead4'] * 1.2  # 提高双冲四防守权重
    elif opp_patterns['dead4'] and opp_patterns['alive3']:
        defense_score += SCORES['dead4_alive3'] * 1.2  # 提高冲四活三防守权重
    elif opp_patterns['alive3'] >= 2:
        defense_score += SCORES['block3'] * 1.5  # 提高双活三防守权重
    else:
        defense_score += (opp_patterns['alive4'] * SCORES['block4'] +
                        opp_patterns['dead4'] * SCORES['dead4'] * 1.2 +
                        opp_patterns['alive3'] * SCORES['block3'] * 1.2 +
                        opp_patterns['dead3'] * SCORES['dead3'] * 1.0 +
                        opp_patterns['alive2'] * SCORES['alive2'] * 0.8 +
                        opp_patterns['dead2'] * SCORES['dead2'] * 0.7)

    # 在某些情况下优先选择防守
    if defense_score > score * 1.1:  # 如果防守分数明显更高
        score = defense_score
    else:
        score = max(score, defense_score * 0.9)  # 否则取较大值但略微降低防守权重
    
    # 位置权重
    center = BOARD_SIZE // 2
    distance_to_center = abs(row - center) + abs(col - center)
    position_weight = max(0, (10 - distance_to_center)) / 10
    score = score * (0.9 + position_weight * 0.1)
    
    # 考虑对手的应对（只在第一层）
    if depth == 0:
        # 模拟这步棋
        board[row][col] = player
        
        # 评估对手最强的应对
        max_opp_score = -float('inf')
        
        # 只考虑周围的位置
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                r, c = row + dr, col + dc
                if (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and 
                    board[r][c] is None):
                    opp_score = evaluate_position(r, c, opponent, 1)
                    max_opp_score = max(max_opp_score, opp_score)
        
        # 撤销模拟
        board[row][col] = None
        
        # 将对手的应对纳入考虑
        if max_opp_score > score:
            score = score * 0.8  # 如果对手有更好的应对，降低当前位置的分数
    
    return score

def ai_move():
    """AI下棋"""
    logger.debug("AI开始思考...")
    best_score = -float('inf')
    best_moves = []
    
    # 获取所有可能的位置
    empty_positions = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if game_state['board'][row][col] is None:
                empty_positions.append((row, col))
    
    logger.debug(f"找到 {len(empty_positions)} 个空位")
    
    # 如果没有可用位置，返回错误
    if not empty_positions:
        logger.error("没有可用位置")
        return None, None
    
    # 如果是第一步，选择靠近中心的位置
    if len(empty_positions) == BOARD_SIZE * BOARD_SIZE:
        center = BOARD_SIZE // 2
        logger.info(f"第一步，选择中心位置 ({center}, {center})")
        return (center, center)
    
    # 找出所有有邻居的空位
    candidates = set()
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if game_state['board'][row][col] is not None:
                # 检查周围三格的位置（扩大搜索范围）
                for dr in range(-3, 4):
                    for dc in range(-3, 4):
                        r, c = row + dr, col + dc
                        if (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and 
                            game_state['board'][r][c] is None):
                            candidates.add((r, c))
    
    logger.debug(f"找到 {len(candidates)} 个候选位置")
    
    # 如果没有找到有邻居的空位，使用所有空位
    if not candidates:
        candidates = set(empty_positions)
        logger.info("使用所有空位作为候选位置")
    
    # 评估每个候选位置
    for row, col in candidates:
        score = evaluate_position(row, col, 'white')
        logger.debug(f"位置 ({row}, {col}) 的评分: {score}")
        if score > best_score:
            best_score = score
            best_moves = [(row, col)]
        elif score == best_score and len(best_moves) < 3:
            best_moves.append((row, col))
    
    # 如果找到了最佳移动
    if best_moves:
        # 如果有必胜/必防位置，直接选择
        if best_score >= SCORES['win5'] * 0.9:
            logger.info(f"找到必胜/必防位置: {best_moves[0]}")
            return best_moves[0]
        # 否则从最佳移动中随机选择一个
        chosen_move = random.choice(best_moves)
        logger.info(f"从最佳移动中随机选择: {chosen_move}, 评分: {best_score}")
        return chosen_move
    
    # 如果没有找到好的位置，随机选择一个空位置
    random_move = random.choice(empty_positions)
    logger.info(f"随机选择位置: {random_move}")
    return random_move

def check_win(row, col):
    """检查是否获胜"""
    board = game_state['board']
    directions = [(1,0), (0,1), (1,1), (1,-1)]
    for dx, dy in directions:
        count = 1
        # 正向检查
        x, y = row + dx, col + dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == board[row][col]:
            count += 1
            x, y = x + dx, y + dy
        # 反向检查
        x, y = row - dx, col - dy
        while 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and board[x][y] == board[row][col]:
            count += 1
            x, y = x - dx, y - dy
        if count >= 5:
            return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.get("/favicon.ico")
def favicon():
    return {"file": static_dir+"/favicon.ico"}  # or: return RedirectResponse("static/favicon.ico")

@app.route('/api/move', methods=['POST'])
def make_move():
    try:
        data = request.get_json()
        row = data['row']
        col = data['col']
        
        logger.info(f"收到玩家移动请求: ({row}, {col})")
        
        # 检查游戏是否已结束
        if game_state['game_over']:
            logger.warning("游戏已结束，拒绝移动")
            return jsonify({'error': '游戏已结束，请重新开始'}), 400
        
        # 检查移动是否有效
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            logger.warning(f"无效的位置: ({row}, {col})")
            return jsonify({'error': '无效的位置'}), 400
        if game_state['board'][row][col] is not None:
            logger.warning(f"位置 ({row}, {col}) 已有棋子")
            return jsonify({'error': '该位置已有棋子'}), 400
        
        # 记录玩家移动
        player_move = {'player': 'black', 'row': row, 'col': col}
        
        # 更新游戏状态（玩家下黑棋）
        game_state['board'][row][col] = 'black'
        game_state['last_move'] = (row, col)
        logger.info(f"玩家下黑棋在 ({row}, {col})")
        
        # 检查玩家是否获胜
        if check_win(row, col):
            game_state['game_over'] = True
            game_state['winner'] = 'black'
            game_state['move_history'].append([player_move, None])  # 记录最后一步
            logger.info("玩家获胜")
            return jsonify({
                'status': 'win',
                'winner': 'black',
                'board': game_state['board'],
                'last_move': game_state['last_move']
            })
        
        # 检查是否平局
        is_full = True
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if game_state['board'][i][j] is None:
                    is_full = False
                    break
            if not is_full:
                break
        
        if is_full:
            game_state['game_over'] = True
            game_state['move_history'].append([player_move, None])  # 记录最后一步
            logger.info("游戏平局")
            return jsonify({
                'status': 'draw',
                'board': game_state['board'],
                'last_move': game_state['last_move']
            })
        
        # AI下棋（白棋）
        logger.info("轮到AI下棋")
        try:
            ai_row, ai_col = ai_move()
            logger.debug(f"AI决定下在位置: ({ai_row}, {ai_col})")
            
            if ai_row is None or ai_col is None:
                logger.error("AI返回了无效的位置")
                return jsonify({'error': 'AI走棋错误'}), 500
            
            if not (0 <= ai_row < BOARD_SIZE and 0 <= ai_col < BOARD_SIZE):
                logger.error(f"AI返回的位置超出边界: ({ai_row}, {ai_col})")
                return jsonify({'error': 'AI走棋错误'}), 500
            
            if game_state['board'][ai_row][ai_col] is not None:
                logger.error(f"AI选择的位置已有棋子: ({ai_row}, {ai_col})")
                return jsonify({'error': 'AI走棋错误'}), 500
            
            # 记录AI移动    
            ai_move_data = {'player': 'white', 'row': ai_row, 'col': ai_col}
            game_state['move_history'].append([player_move, ai_move_data])  # 记录这一轮的移动
                
            game_state['board'][ai_row][ai_col] = 'white'
            game_state['last_move'] = (ai_row, ai_col)
            logger.info(f"AI下白棋在 ({ai_row}, {ai_col})")
            
            # 检查AI是否获胜
            if check_win(ai_row, ai_col):
                game_state['game_over'] = True
                game_state['winner'] = 'white'
                logger.info("AI获胜")
                return jsonify({
                    'status': 'win',
                    'winner': 'white',
                    'board': game_state['board'],
                    'last_move': game_state['last_move']
                })
            
            return jsonify({
                'status': 'continue',
                'board': game_state['board'],
                'current_player': 'black',
                'last_move': game_state['last_move']
            })
            
        except Exception as ai_error:
            logger.error(f"AI走棋时发生错误: {str(ai_error)}", exc_info=True)
            return jsonify({'error': 'AI走棋错误'}), 500
        
    except Exception as e:
        logger.error(f"处理移动请求时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '服务器错误'}), 500

@app.route('/api/reset', methods=['POST'])
def reset_game():
    try:
        logger.info("重置游戏")
        game_state['board'] = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        game_state['current_player'] = 'black'
        game_state['game_over'] = False
        game_state['winner'] = None
        game_state['last_move'] = None
        game_state['move_history'] = []  # 清空移动历史
        
        return jsonify({
            'status': 'reset',
            'board': game_state['board'],
            'current_player': 'black',
            'game_over': False,
            'winner': None,
            'last_move': None
        })
    except Exception as e:
        logger.error(f"重置游戏时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '重置游戏失败'}), 500

@app.route('/api/undo', methods=['POST'])
def undo_move():
    try:
        logger.info("收到悔棋请求")
        
        # 检查是否有可以悔棋的步骤
        if not game_state['move_history']:
            logger.warning("没有可以悔棋的步骤")
            return jsonify({'error': '没有可以悔棋的步骤'}), 400
            
        # 检查游戏是否已结束
        if game_state['game_over']:
            logger.warning("游戏已结束，不能悔棋")
            return jsonify({'error': '游戏已结束，不能悔棋'}), 400
            
        # 获取最后一组移动
        last_moves = game_state['move_history'].pop()
        player_move, ai_move = last_moves
        
        # 撤销移动
        game_state['board'][player_move['row']][player_move['col']] = None
        if ai_move:
            game_state['board'][ai_move['row']][ai_move['col']] = None
            
        # 更新最后一步位置
        if game_state['move_history']:
            last_round = game_state['move_history'][-1]
            game_state['last_move'] = (last_round[1]['row'], last_round[1]['col']) if last_round[1] else (last_round[0]['row'], last_round[0]['col'])
        else:
            game_state['last_move'] = None
            
        logger.info("悔棋成功")
        return jsonify({
            'status': 'success',
            'board': game_state['board'],
            'current_player': 'black',
            'last_move': game_state['last_move']
        })
        
    except Exception as e:
        logger.error(f"悔棋时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '悔棋失败'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=6688) 