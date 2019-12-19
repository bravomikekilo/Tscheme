(define (zip l1 l2) (match l1
    [(Cons x xs) (match l2
                    [(Cons y ys) (cons (tuple x y) (zip xs ys))]
                    [(Nil) null])]
    [(Nil) null]))