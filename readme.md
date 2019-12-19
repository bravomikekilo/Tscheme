### a experiment implementation of typed scheme


## 项目结构
项目主要使用Python进行实现
所需要的Python 版本是3.6及以上
所需的依赖包仅有一个， 列写在**requirements.txt**中。可以通过以下命令安装
```shell script
pip3 install -r requirements.txt
```
生成的代码可以在标准的racket 7.5环境下运行

## 使用说明
项目提供了两个可执行脚本type_check.py, compiler.py

- type_check.py 用来对程序进行类型检查
- compiler.py 用来对程序进行编译

### type_check
type_check.py 使用样例
```shell script
    python3 type_check.py test_src/list/flatten.rkt
```

type_check.py 的样例输出
```
define: foldr :: forall m.n => (n -> m -> m) -> m -> List n -> m
define: concat :: forall u => List u -> List u -> List u
define: flatten :: forall bf => List (List bf) -> List bf
define: length :: forall bo => List bo -> Number
define: nest :: List (List Number)
expr: (println (flatten nest)) :: Unit
expr: (println (length (flatten nest))) :: Unit
```
可以看到type_check显示了每个顶级define和表达式的类型

### compiler

compiler.py 使用样例
```shell script
    python3 compiler.py test_src/list/flatten.rkt
```

compiler.py 默认输出的路径是out.rkt
可以使用
```shell script
    # 直接执行
    racket out.rkt

    # 或运行后进入交互式环境
    racket -i out.rkt
```

典型的编译输出
```lisp
#lang racket

(define (foldr f x0 l)
  (match l [(cons x xs)
             (f x (foldr f x0 xs))]
    ['() 
      x0]))
(define (concat x y)
  (foldr cons y x))
(define (flatten x)
  (foldr (lambda (l r)
           (concat l r))
    null x))
(define (length x)
  (foldr (lambda (l r)
           (+ r 1))
    0 x))
(define nest '((1 2 3)
                (2 3)
                (1)))
(println (flatten nest))
(println (length (flatten nest)))

```

### 项目的实现功能
项目实现了基本的Hindley-Milner类型系统和类型检查功能
实现的基本类型有 Unit类型(C语言中的void), Number类型, Bool类型， String类型， Symbol类型

实现的其他类型有

- 函数类型
- 和类型
- 元组类型

在和类型的基础上,我们对scheme中的list进行了建模, 提供了 List类型

项目实现的语法有: if, cond, apply, let, define, set!, begin, list, tuple, match

基于我们自己设计的基于类型的match语法,我们实现现代语言中的
一个重要特性 **模式匹配**

一个常见的patten match
```lisp
(define (foldr f x0 l) (match l
    [(Cons x xs) (f x (foldr f x0 xs))]
    [(Nil) x0]
))


```
