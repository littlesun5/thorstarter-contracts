# ChromeDriver PATH环境变量配置说明

## Linux系统配置PATH

### 方法1：安装到系统路径（推荐，自动在PATH中）

```bash
# 下载ChromeDriver后，解压
unzip chromedriver_linux64.zip

# 移动到系统路径（已经在PATH中）
sudo mv chromedriver /usr/local/bin/

# 设置执行权限
sudo chmod +x /usr/local/bin/chromedriver

# 验证（应该可以直接运行）
chromedriver --version
```

**说明**：`/usr/local/bin/` 已经在系统的PATH中，所以不需要手动配置。

### 方法2：安装到自定义路径并添加到PATH

#### 步骤1：创建目录并复制文件
```bash
# 创建目录
mkdir -p ~/bin

# 复制chromedriver到该目录
cp chromedriver ~/bin/

# 设置权限
chmod +x ~/bin/chromedriver
```

#### 步骤2：添加到PATH（永久生效）

编辑 `~/.bashrc` 文件：
```bash
nano ~/.bashrc
```

在文件末尾添加：
```bash
export PATH="$HOME/bin:$PATH"
```

保存后，运行：
```bash
source ~/.bashrc
```

#### 步骤3：验证
```bash
chromedriver --version
```

### 方法3：临时添加到PATH（仅当前终端会话）

```bash
export PATH="$PATH:/path/to/chromedriver"
chromedriver --version
```

**注意**：关闭终端后失效。

---

## Windows系统配置PATH

### 方法1：通过系统设置（推荐，永久生效）

#### 步骤1：准备ChromeDriver
1. 下载 `chromedriver.exe`
2. 创建一个文件夹，例如：`C:\ChromeDriver\`
3. 将 `chromedriver.exe` 复制到该文件夹

#### 步骤2：添加到系统PATH
1. **打开环境变量设置**：
   - 按 `Win + R`，输入 `sysdm.cpl`，回车
   - 或：右键"此电脑" → 属性 → 高级系统设置 → 环境变量

2. **编辑PATH变量**：
   - 在"系统变量"区域找到 `Path`
   - 点击"编辑"
   - 点击"新建"
   - 输入：`C:\ChromeDriver\`（你的ChromeDriver路径）
   - 点击"确定"保存所有窗口

3. **验证**：
   - 打开**新的**命令提示符（重要：必须新开）
   - 输入：`chromedriver --version`
   - 如果显示版本号，说明配置成功

### 方法2：通过命令行（需要管理员权限）

```cmd
# 以管理员身份运行命令提示符，然后执行：
setx PATH "%PATH%;C:\ChromeDriver\" /M
```

**注意**：需要重启命令提示符才能生效。

### 方法3：临时添加到PATH（仅当前会话）

```cmd
set PATH=%PATH%;C:\ChromeDriver\
chromedriver --version
```

**注意**：关闭命令提示符后失效。

### 方法4：放在Python脚本同目录（最简单）

1. 将 `chromedriver.exe` 放在与 `btc_price_monitor.py` 相同的文件夹
2. 修改脚本，指定chromedriver路径（我会更新脚本支持这个）

---

## macOS系统配置PATH

### 方法1：使用Homebrew（推荐）
```bash
brew install chromedriver
```
自动配置，无需手动设置PATH。

### 方法2：手动安装
```bash
# 下载并解压后
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

`/usr/local/bin/` 已经在PATH中，无需额外配置。

---

## 验证PATH配置

### Linux/macOS
```bash
# 检查chromedriver是否在PATH中
which chromedriver

# 检查PATH变量
echo $PATH

# 测试运行
chromedriver --version
```

### Windows
```cmd
# 检查chromedriver是否在PATH中
where chromedriver

# 检查PATH变量
echo %PATH%

# 测试运行
chromedriver --version
```

---

## 快速检查脚本

我已经创建了检查脚本，运行：
```bash
./检查环境.sh
```

这会自动检查所有环境配置。

---

## 常见问题

### Q: 添加PATH后还是找不到chromedriver？
A: 
- Windows：必须**重新打开**命令提示符
- Linux/macOS：运行 `source ~/.bashrc` 或重新打开终端

### Q: 不想配置PATH怎么办？
A: 可以将chromedriver放在脚本同目录，或使用webdriver-manager（自动管理）

### Q: 如何查看当前PATH？
A:
- Linux/macOS: `echo $PATH`
- Windows: `echo %PATH%`

### Q: 多个路径如何分隔？
A:
- Linux/macOS: 用冒号 `:` 分隔，如：`PATH="/usr/bin:/usr/local/bin:$HOME/bin"`
- Windows: 用分号 `;` 分隔，如：`PATH=C:\Windows;C:\ChromeDriver\`

---

## 推荐方案

**最简单的方法**：使用 `webdriver-manager` Python包，自动下载和管理ChromeDriver，无需手动配置PATH。

```bash
pip install webdriver-manager
```

然后脚本会自动使用它（我会更新脚本支持）。
