(define-sum (Nest a)
    [Nest a (Nest (List a))]
    [None]
)

(define nested
    (Nest.Nest 1
        (Nest.Nest
            '(2 3 4)
            (Nest.Nest '((1 2 3) (4 5) (6 3 4 5)) Nest.None)))
)


(define (deepth [n (Nest a)]) Number (match n
    [(Nest.None) 0]
    [(Nest.Nest _ xs) (+ 1 (deepth xs))]
))

(print (deepth nested))