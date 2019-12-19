(define-sum (Tree a)
    [Branch a (Tree a) (Tree a)]
    [Leaf a])

(define (concat x y) (match x
    [(Cons x xs) (cons x (concat xs y))]
    [(Nil) y]
))

(define (pre-order t) (match t
    [(Tree.Branch v left right) (cons v (concat (pre-order left) (pre-order right)))]
    [(Tree.Leaf x) (cons x null)]))


(define (in-order t) (match t
    [(Tree.Branch v left right) (concat (in-order left) (cons v (in-order right)))]
    [(Tree.Leaf x) (cons x null)]))


(define (post-order t) (match t
    [(Tree.Branch v left right) (concat
                                  (post-order left)
                                  (concat
                                    (post-order right)
                                    (cons v null)))]
    [(Tree.Leaf x) (cons x null)]))
