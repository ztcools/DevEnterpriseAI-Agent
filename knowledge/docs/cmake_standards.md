# CMake编译规范

## 1. 项目结构

```
project/
├── CMakeLists.txt          # 主CMake配置文件
├── src/                    # 源代码目录
│   ├── CMakeLists.txt
│   └── ...
├── include/                # 头文件目录
├── tests/                  # 测试代码目录
│   └── CMakeLists.txt
├── docs/                   # 文档目录
├── build/                  # 构建目录（自动生成）
└── third_party/            # 第三方依赖
```

## 2. CMakeLists.txt编写规范

### 2.1 基本结构
```cmake
cmake_minimum_required(VERSION 3.16)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(my_app src/main.cpp)
target_link_libraries(my_app PRIVATE ${LIBS})
```

### 2.2 编译选项
- 开发环境使用Debug模式：`cmake -DCMAKE_BUILD_TYPE=Debug ..`
- 生产环境使用Release模式：`cmake -DCMAKE_BUILD_TYPE=Release ..`

### 2.3 常用变量
- `CMAKE_BUILD_TYPE`: 构建类型 (Debug/Release)
- `CMAKE_INSTALL_PREFIX`: 安装路径
- `BUILD_TESTING`: 是否构建测试

## 3. 编译流程

### 3.1 标准编译步骤
```bash
# 创建构建目录
mkdir -p build && cd build

# 配置CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
make -j$(nproc)

# 安装
make install
```

### 3.2 交叉编译
```bash
cmake .. \
  -DCMAKE_TOOLCHAIN_FILE=../toolchain.cmake \
  -DCMAKE_BUILD_TYPE=Release
```

## 4. 常见问题

### 4.1 找不到头文件
- 检查 `include_directories()` 是否正确设置
- 确保头文件路径正确

### 4.2 链接错误
- 检查 `target_link_libraries()` 顺序
- 确保库已正确安装

### 4.3 版本不兼容
- 检查CMake最低版本要求
- 更新CMake或降级项目配置