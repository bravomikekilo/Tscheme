(define (foldl f x0 l) (match l
    [(Cons x xs) (foldl f (f x0 x) xs)]
    [(Null) x0]
))