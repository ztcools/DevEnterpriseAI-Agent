# 历史编译报错解决方案

## 1. 链接错误

### 1.1 undefined reference to `xxx'

**错误描述**:
```
/usr/bin/ld: CMakeFiles/my_app.dir/src/main.cpp.o: in function `main':
main.cpp:(.text+0x10): undefined reference to `MyClass::MyClass()'
collect2: error: ld returned 1 exit status
```

**解决方案**:
1. 检查头文件是否正确包含
2. 确认源文件是否已添加到CMakeLists.txt
3. 检查链接库顺序是否正确

**修复示例**:
```cmake
# 在CMakeLists.txt中添加源文件
add_executable(my_app
  src/main.cpp
  src/MyClass.cpp  # 添加缺失的源文件
)
```

### 1.2 cannot find -lxxx

**错误描述**:
```
/usr/bin/ld: cannot find -lboost_system
collect2: error: ld returned 1 exit status
```

**解决方案**:
1. 检查库是否已安装
2. 设置正确的库搜索路径
3. 使用 `find_package()` 自动查找库

**修复示例**:
```bash
# 安装缺失的库
sudo apt-get install libboost-system-dev
```

## 2. 编译错误

### 2.1 ‘xxx’ was not declared in this scope

**错误描述**:
```
src/main.cpp:10:5: error: ‘MyClass’ was not declared in this scope
   MyClass obj;
   ^~~~~~~
```

**解决方案**:
1. 检查头文件是否正确包含
2. 确认命名空间是否正确使用
3. 检查头文件保护宏

**修复示例**:
```cpp
// 添加缺失的头文件
#include "MyClass.hpp"
```

### 2.2 invalid use of incomplete type ‘class xxx’

**错误描述**:
```
src/main.cpp:15:10: error: invalid use of incomplete type ‘class MyClass’
   obj.doSomething();
        ^~~~~~~~~~~
```

**解决方案**:
1. 添加头文件包含
2. 检查前向声明是否正确

### 2.3 no matching function for call to ‘xxx’

**错误描述**:
```
src/main.cpp:10:20: error: no matching function for call to ‘MyClass::MyClass(int)’
   MyClass obj(42);
                    ^
```

**解决方案**:
1. 检查构造函数签名
2. 确认参数类型和数量正确

## 3. CMake配置错误

### 3.1 CMake Error at CMakeLists.txt:10 (project):

**错误描述**:
```
CMake Error at CMakeLists.txt:10 (project):
  Running
    '/usr/bin/cmake' '-E' 'cmake_depends' 'Unix Makefiles' ...
  failed with error code 1.
```

**解决方案**:
1. 删除build目录重新构建
2. 检查CMakeLists.txt语法

**修复示例**:
```bash
rm -rf build && mkdir build && cd build
cmake ..
```

### 3.2 Could NOT find xxx

**错误描述**:
```
CMake Error at /usr/share/cmake-3.16/Modules/FindPackageHandleStandardArgs.cmake:146 (message):
  Could NOT find Boost (missing: system)
```

**解决方案**:
1. 安装缺失的依赖包
2. 设置正确的环境变量

## 4. 运行时错误

### 4.1 error while loading shared libraries

**错误描述**:
```
./my_app: error while loading shared libraries: libboost_system.so.1.71.0: cannot open shared object file: No such file or directory
```

**解决方案**:
1. 设置 `LD_LIBRARY_PATH` 环境变量
2. 将库安装到系统路径

**修复示例**:
```bash
export LD_LIBRARY_PATH=/path/to/library:$LD_LIBRARY_PATH
./my_app
```