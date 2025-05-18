######################################
##  pip3 install pysdl2 pysdl2-dll  ##
##  AI 生成的代码                    ##
######################################
import sdl2
import sdl2.ext
import sdl2.sdlttf as ttf
import sys
import math

# 坐标转换代码
i_x = 1
i_y = 0.5
j_x = -1
j_y = 0.5
w = 32
h = 32

def to_screen_coordinate(tile):
    """转换网格坐标为屏幕坐标"""
    x = tile[0] * i_x * 0.5 * w + tile[1] * j_x * 0.5 * w
    y = tile[0] * i_y * 0.5 * h + tile[1] * j_y * 0.5 * h
    return (x, y)

def invert_matrix(a, b, c, d):
    """计算2x2矩阵的逆矩阵"""
    det = 1 / (a * d - b * c)
    return {
        'a': det * d,
        'b': det * -b,
        'c': det * -c,
        'd': det * a,
    }

def to_grid_coordinate(screen):
    """转换屏幕坐标为网格坐标"""
    a = i_x * 0.5 * w
    b = j_x * 0.5 * w
    c = i_y * 0.5 * h
    d = j_y * 0.5 * h
    inv = invert_matrix(a, b, c, d)
    x = screen[0] * inv['a'] + screen[1] * inv['b']
    y = screen[0] * inv['c'] + screen[1] * inv['d']
    return (x, y)

class Tile:
    """地图瓦片类"""
    def __init__(self, tile_type, color):
        self.tile_type = tile_type
        self.color = color

class IsometricMap:
    """等距地图类"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = {}
        self.selected_tile = (0, 0)
        self.current_tile_type = "grass"
        self.tile_types = {
            "grass": Tile("grass", (0, 200, 0)),
            "water": Tile("water", (0, 0, 200)),
            "mountain": Tile("mountain", (150, 150, 150)),
            "forest": Tile("forest", (0, 100, 0))
        }
        
    def get_tile(self, grid_pos):
        return self.tiles.get(grid_pos, None)
    
    def set_tile(self, grid_pos, tile_type):
        if 0 <= grid_pos[0] < self.width and 0 <= grid_pos[1] < self.height:
            self.tiles[grid_pos] = self.tile_types[tile_type]
    
    def render(self, renderer, camera_x=0, camera_y=0, zoom=1.0):
        """渲染地图，考虑相机偏移和缩放"""
        for x in range(self.width):
            for y in range(self.height):
                tile = self.get_tile((x, y))
                if tile:
                    screen_pos = to_screen_coordinate((x, y))
                    # 应用相机偏移和缩放
                    pos_x = screen_pos[0] * zoom + camera_x
                    pos_y = screen_pos[1] * zoom + camera_y
                    self._render_tile(renderer, (pos_x, pos_y), tile.color, zoom)
        
        # 渲染选中的瓦片
        screen_pos = to_screen_coordinate(self.selected_tile)
        pos_x = screen_pos[0] * zoom + camera_x
        pos_y = screen_pos[1] * zoom + camera_y
        self._render_tile(renderer, (pos_x, pos_y), (255, 255, 0), zoom, True)
    
    def _render_tile(self, renderer, pos, color, zoom, selected=False):
        """渲染单个瓦片，考虑缩放"""
        # 使用更兼容的方法绘制填充的菱形
        sdl2.SDL_SetRenderDrawColor(renderer, *color, 255)
        
        # 根据缩放调整瓦片大小，确保为整数
        half_w = int(w * zoom // 2)
        half_h = int(h * zoom // 4)
        
        points = [
            (int(pos[0]), int(pos[1] - half_h)),  # 上顶点
            (int(pos[0] + half_w), int(pos[1])),  # 右顶点
            (int(pos[0]), int(pos[1] + half_h)),  # 下顶点
            (int(pos[0] - half_w), int(pos[1]))   # 左顶点
        ]
        
        # 使用三角形扇面算法绘制填充的菱形
        self._fill_polygon(renderer, points)
        
        # 绘制边框
        if selected:
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 0, 255)
        else:
            dark_color = tuple(max(c - 50, 0) for c in color)
            sdl2.SDL_SetRenderDrawColor(renderer, *dark_color, 255)
            
        sdl2.SDL_RenderDrawLine(renderer, points[0][0], points[0][1], points[1][0], points[1][1])
        sdl2.SDL_RenderDrawLine(renderer, points[1][0], points[1][1], points[2][0], points[2][1])
        sdl2.SDL_RenderDrawLine(renderer, points[2][0], points[2][1], points[3][0], points[3][1])
        sdl2.SDL_RenderDrawLine(renderer, points[3][0], points[3][1], points[0][0], points[0][1])
    
    def _fill_polygon(self, renderer, points):
        """使用三角形扇面算法填充多边形"""
        if len(points) < 3:
            return
            
        # 以第一个点为中心，将多边形分解为多个三角形
        for i in range(1, len(points) - 1):
            self._fill_triangle(renderer, points[0], points[i], points[i+1])
    
    def _fill_triangle(self, renderer, p1, p2, p3):
        """填充三角形"""
        # 使用扫描线算法填充三角形
        # 首先按y坐标排序三个顶点，并确保为整数
        points = sorted([p1, p2, p3], key=lambda p: p[1])
        
        y_min = int(points[0][1])
        y_mid = int(points[1][1])
        y_max = int(points[2][1])
        
        # 三角形顶部（平顶）
        if y_min < y_mid:
            dx1 = (points[1][0] - points[0][0]) / (y_mid - y_min) if (y_mid - y_min) != 0 else 0
            dx2 = (points[2][0] - points[0][0]) / (y_max - y_min) if (y_max - y_min) != 0 else 0
            
            x1 = points[0][0]
            x2 = points[0][0]
            
            for y in range(y_min, y_mid):
                sdl2.SDL_RenderDrawLine(renderer, int(x1), y, int(x2), y)
                x1 += dx1
                x2 += dx2
        
        # 三角形底部（平底）
        if y_mid < y_max:
            dx1 = (points[2][0] - points[1][0]) / (y_max - y_mid) if (y_max - y_mid) != 0 else 0
            dx2 = (points[2][0] - points[0][0]) / (y_max - y_min) if (y_max - y_min) != 0 else 0
            
            x1 = points[1][0]
            x2 = points[0][0] + dx2 * (y_mid - y_min)
            
            for y in range(y_mid, y_max):
                sdl2.SDL_RenderDrawLine(renderer, int(x1), y, int(x2), y)
                x1 += dx1
                x2 += dx2

class IsometricMapEditor:
    """等距地图编辑器"""
    def __init__(self, width=800, height=600):
        # 初始化SDL2
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) < 0:
            raise RuntimeError(f"SDL初始化失败: {sdl2.SDL_GetError()}")
        
        # 初始化TTF
        if ttf.TTF_Init() < 0:
            raise RuntimeError(f"TTF初始化失败: {ttf.TTF_GetError()}")
        
        # 创建窗口
        self.window = sdl2.SDL_CreateWindow(
            b"Isometric Map Editor",
            sdl2.SDL_WINDOWPOS_CENTERED, 
            sdl2.SDL_WINDOWPOS_CENTERED,
            width, height, 
            sdl2.SDL_WINDOW_SHOWN
        )
        if not self.window:
            raise RuntimeError(f"窗口创建失败: {sdl2.SDL_GetError()}")
        
        # 创建渲染器
        self.renderer = sdl2.SDL_CreateRenderer(self.window, -1, sdl2.SDL_RENDERER_ACCELERATED)
        if not self.renderer:
            raise RuntimeError(f"渲染器创建失败: {sdl2.SDL_GetError()}")
        
        # 尝试加载多种字体
        self.font = None
        font_names = ["simhei.ttf", "simsun.ttc", "microsoftyahei.ttf", "arial.ttf"]
        
        for font_name in font_names:
            try:
                self.font = ttf.TTF_OpenFont(font_name.encode('utf-8'), 24)
                if self.font:
                    print(f"成功加载字体: {font_name}")
                    break
            except Exception as e:
                print(f"尝试加载字体 {font_name} 失败: {e}")
        
        # 如果所有字体加载失败，禁用文本渲染
        if not self.font:
            print("警告: 无法加载任何字体，文本UI将不可用")
            self.font = None
        
        # 创建地图
        self.map = IsometricMap(15, 15)
        
        # 相机控制
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # 界面状态
        self.running = True
        self.show_help = False
        
        # 初始化一些瓦片
        for x in range(15):
            for y in range(15):
                if x < 5:
                    self.map.set_tile((x, y), "water")
                elif x < 10:
                    self.map.set_tile((x, y), "grass")
                else:
                    self.map.set_tile((x, y), "forest")
    
    def run(self):
        """运行主循环"""
        while self.running:
            self._handle_events()
            self._render()
    
    def _handle_events(self):
        """处理事件"""
        event = sdl2.SDL_Event()
        while sdl2.SDL_PollEvent(event):
            if event.type == sdl2.SDL_QUIT:
                self.running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                self._handle_key_event(event.key.keysym.sym)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN:
                self._handle_mouse_click(event.button)
            elif event.type == sdl2.SDL_MOUSEMOTION:
                self._handle_mouse_move(event.motion)
    
    def _handle_key_event(self, key):
        """处理键盘事件"""
        if key == sdl2.SDLK_ESCAPE:
            self.running = False
        elif key == sdl2.SDLK_h:
            self.show_help = not self.show_help
        elif key == sdl2.SDLK_UP:
            self.camera_y -= 20
        elif key == sdl2.SDLK_DOWN:
            self.camera_y += 20
        elif key == sdl2.SDLK_LEFT:
            self.camera_x -= 20
        elif key == sdl2.SDLK_RIGHT:
            self.camera_x += 20
        elif key == sdl2.SDLK_EQUALS:  # + 键
            self.zoom = min(2.0, self.zoom * 1.1)
        elif key == sdl2.SDLK_MINUS:
            self.zoom = max(0.5, self.zoom * 0.9)
        elif key == sdl2.SDLK_1:
            self.map.current_tile_type = "grass"
        elif key == sdl2.SDLK_2:
            self.map.current_tile_type = "water"
        elif key == sdl2.SDLK_3:
            self.map.current_tile_type = "mountain"
        elif key == sdl2.SDLK_4:
            self.map.current_tile_type = "forest"
    
    def _handle_mouse_click(self, button):
        """处理鼠标点击事件"""
        if button.button == sdl2.SDL_BUTTON_LEFT:
            # 获取鼠标在屏幕上的坐标
            screen_x = button.x
            screen_y = button.y
            
            # 转换为游戏世界坐标（考虑相机偏移和缩放）
            world_x = (screen_x - self.camera_x) / self.zoom
            world_y = (screen_y - self.camera_y) / self.zoom
            
            # 转换为网格坐标
            grid_x, grid_y = to_grid_coordinate((world_x, world_y))
            
            # 确保坐标在整数网格上
            grid_pos = (int(grid_x), int(grid_y))
            
            # 检查坐标是否在地图范围内
            if 0 <= grid_pos[0] < self.map.width and 0 <= grid_pos[1] < self.map.height:
                print(f"放置瓦片到: {grid_pos}")  # 调试输出
                self.map.set_tile(grid_pos, self.map.current_tile_type)
            else:
                print(f"点击位置超出地图范围: {grid_pos}")  # 调试输出
    
    def _handle_mouse_move(self, motion):
        """处理鼠标移动事件"""
        screen_x = motion.x
        screen_y = motion.y
        grid_pos = self._screen_to_world((screen_x, screen_y))
        
        # 确保选中的瓦片在地图范围内
        if 0 <= grid_pos[0] < self.map.width and 0 <= grid_pos[1] < self.map.height:
            self.map.selected_tile = (int(grid_pos[0]), int(grid_pos[1]))
    
    def _screen_to_world(self, screen_pos):
        """考虑相机偏移和缩放后的屏幕坐标转世界坐标"""
        # 应用相机偏移和缩放的逆变换
        world_x = (screen_pos[0] - self.camera_x) / self.zoom
        world_y = (screen_pos[1] - self.camera_y) / self.zoom
        
        # 调用原始的坐标转换函数
        grid_pos = to_grid_coordinate((world_x, world_y))
        return grid_pos
    
    def _render(self):
        """渲染场景"""
        # 清屏
        sdl2.SDL_SetRenderDrawColor(self.renderer, 240, 240, 240, 255)
        sdl2.SDL_RenderClear(self.renderer)
        
        # 渲染地图（直接应用相机参数，不使用SDL_RenderTranslate）
        self.map.render(self.renderer, self.camera_x, self.camera_y, self.zoom)
        
        # 渲染UI
        self._render_ui()
        
        # 刷新屏幕
        sdl2.SDL_RenderPresent(self.renderer)
    
    def _render_ui(self):
        """渲染用户界面"""
        if self.font:
            # 渲染当前选中的瓦片类型
            self._render_text(f"Current Tile: {self.map.current_tile_type}", 10, 10)
            
            # 渲染帮助信息
            if self.show_help:
                help_text = [
                    "Help:",
                    "Arrow Keys: Move View",
                    "+/-: Zoom",
                    "1-4: Select Tile Type",
                    "H: Show/Hide Help",
                    "Mouse: Select and Place Tiles",
                    "ESC: Exit"
                ]
                
                for i, text in enumerate(help_text):
                    self._render_text(text, 10, 40 + i * 25)
        else:
            # 如果字体加载失败，渲染简化的UI
            self._render_simplified_ui()
    
    def _render_text(self, text, x, y):
        """渲染文本"""
        if not self.font:
            return
        
        text_bytes = text.encode('utf-8')
        text_surface = ttf.TTF_RenderUTF8_Solid(self.font, text_bytes, 
                                               sdl2.SDL_Color(0, 0, 0, 255))
        if not text_surface:
            return
        
        text_texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, text_surface)
        sdl2.SDL_FreeSurface(text_surface)
        
        if text_texture:
            rect = sdl2.SDL_Rect(x, y, 0, 0)
            sdl2.SDL_QueryTexture(text_texture, None, None, rect.w, rect.h)
            sdl2.SDL_RenderCopy(self.renderer, text_texture, None, rect)
            sdl2.SDL_DestroyTexture(text_texture)
    
    def _render_simplified_ui(self):
        """在字体不可用时渲染简化的UI"""
        # 渲染当前瓦片类型指示器
        tile_type = self.map.current_tile_type
        color = self.map.tile_types[tile_type].color
        
        # 绘制一个小方块表示当前瓦片类型
        sdl2.SDL_SetRenderDrawColor(self.renderer, *color, 255)
        rect = sdl2.SDL_Rect(10, 10, 20, 20)
        sdl2.SDL_RenderFillRect(self.renderer, rect)
        
        # 绘制帮助提示图标
        if self.show_help:
            # 绘制方向键图标
            self._render_direction_icons()
            
            # 绘制数字键图标
            self._render_number_icons()
    
    def _render_direction_icons(self):
        """绘制方向键图标"""
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        
        # 上箭头
        points = [(50, 10), (55, 20), (45, 20)]
        for i in range(len(points) - 1):
            sdl2.SDL_RenderDrawLine(renderer, points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        sdl2.SDL_RenderDrawLine(renderer, points[-1][0], points[-1][1], points[0][0], points[0][1])
        
        # 下箭头
        points = [(70, 20), (75, 10), (65, 10)]
        for i in range(len(points) - 1):
            sdl2.SDL_RenderDrawLine(renderer, points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        sdl2.SDL_RenderDrawLine(renderer, points[-1][0], points[-1][1], points[0][0], points[0][1])
        
        # 左箭头
        points = [(90, 15), (100, 10), (100, 20)]
        for i in range(len(points) - 1):
            sdl2.SDL_RenderDrawLine(renderer, points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        sdl2.SDL_RenderDrawLine(renderer, points[-1][0], points[-1][1], points[0][0], points[0][1])
        
        # 右箭头
        points = [(110, 10), (120, 15), (110, 20)]
        for i in range(len(points) - 1):
            sdl2.SDL_RenderDrawLine(renderer, points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        sdl2.SDL_RenderDrawLine(renderer, points[-1][0], points[-1][1], points[0][0], points[0][1])
    
    def _render_number_icons(self):
        """绘制数字1-4的简单表示"""
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        
        for i in range(4):
            x = 140 + i * 30
            y = 10
            
            # 绘制数字1的竖线
            sdl2.SDL_RenderDrawLine(renderer, x, y, x, y+20)
            
            # 绘制数字2-4的横线
            if i > 0:
                sdl2.SDL_RenderDrawLine(renderer, x-5, y+10, x+5, y+10)
            if i > 1:
                sdl2.SDL_RenderDrawLine(renderer, x-5, y+15, x+5, y+15)
            if i > 2:
                sdl2.SDL_RenderDrawLine(renderer, x-5, y+5, x+5, y+5)
    
    def cleanup(self):
        """清理资源"""
        if self.font:
            ttf.TTF_CloseFont(self.font)
        ttf.TTF_Quit()
        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

def main():
    """主函数"""
    try:
        editor = IsometricMapEditor()
        editor.run()
        editor.cleanup()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())