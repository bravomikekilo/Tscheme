(define-sum (Tree a)
    [Branch a (Tree a) (Tree a)]
    [Leaf a])

(define (tree-map f t) (match t
    [(Tree.Branch v left right) (Tree.Branch (f v) (tree-map f left) (tree-map f right))]
    [(Tree.Leaf v) (Tree.Leaf (f v))]
))
