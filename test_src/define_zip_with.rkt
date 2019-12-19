(define (zipwith l1 l2 f) (match l1
    [(Cons x xs) (match l2
                    [(Cons y ys) (cons (f x y) (zipwith xs ys f))]
                    [(Nil) null]
                    )]
    [(Nil) null]))