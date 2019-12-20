(define-sum (Term a)
  [Add (Term a) (Term a) ]
  [Sub (Term a) (Term a) ]
  [Mul (Term a) (Term a) ]
  [Div (Term a) (Term a) ]
  [Val Number])

(define (eval-term term)
  (match term
	 [(Term.Add x y) (add-term x y)]
	 [(Term.Sub x y) (sub-term x y)]
	 [(Term.Mul x y) (mul-term x y)]
	 [(Term.Div x y) (div-term x y)]
	 [(Term.Val x) x]))

(define (term-combiner f)
  (lambda (x y)
    (f (eval-term x)
       (eval-term y))))

(define add-term (term-combiner +))
(define sub-term (term-combiner -))
(define mul-term (term-combiner *))
(define div-term (term-combiner /))

(define tree-1
  (Term.Div (Term.Add (Term.Val 6)
		      (Term.Mul (Term.Val 2)
				(Term.Val 3)))
	    (Term.Sub (Term.Val 5)
		      (Term.Val 1))))

(print (eval-term tree-1))