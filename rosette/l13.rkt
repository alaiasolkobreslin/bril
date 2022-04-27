#lang rosette

(require rosette/lib/angelic rosette/lib/destruct)

; arithmetic
(struct iffy (condition true false) #:transparent)
(struct plus (left right) #:transparent)
(struct minus (left right) #:transparent)
(struct mul (left right) #:transparent)
(struct div (left right) #:transparent)
(struct shift (left right) #:transparent)
(struct square (arg) #:transparent)
(struct neg (arg) #:transparent)
(struct absolute (arg) #:transparent)

; boolean
(struct eq (left right) #:transparent)
(struct lt (left right) #:transparent)
(struct gt (left right) #:transparent)


(define prog (plus (square 7) 3))

(define (interpret p)
  (destruct p
    [(iffy a b c) (if (interpret a) (interpret b) (interpret c))]
    [(plus a b)   (+ (interpret a) (interpret b))]
    [(minus a b)  (- (interpret a) (interpret b))]
    [(mul a b)    (* (interpret a) (interpret b))]
    [(div a b)    (/ (interpret a) (interpret b))]
    [(shift a b)  (arithmetic-shift (interpret a) (interpret b))]
    [(square a)   (expt (interpret a) 2)]
    [(neg a)      (- (interpret a))]
    [(absolute a) (abs (interpret a))]

    [(eq a b)      (= (interpret a) (interpret b))]
    [(lt a b)      (< (interpret a) (interpret b))]
    [(gt a b)      (> (interpret a) (interpret b))]
    [_ p]))

; Compute the absolute value of `x`.
(define (absv x)
  (if (< x 0) (- x) x))

(interpret prog)

; Define a symbolic variable called y of type integer.
(define-symbolic y integer?)

(define-symbolic x c integer?)

(solve 
  (assert 
    (= (interpret (square (plus y 2))) 25)))

(synthesize
  #:forall (list x)
  #:guarantee (assert (= (interpret (mul c x)) (+ x x))))


(define (??expr terminals)
  (define a (apply choose* terminals))
  (define b (apply choose* terminals))
  (choose*  a
            (neg a)
            (plus a b)
            (minus a b)
            (mul a b)
            (div a b)
            (shift a b)
            (square a)
            (absolute a)

            (eq a b)
            (lt a b)
            (gt a b)))

; (define-symbolic p q integer?)  ; get access to more constants
; (define sketch
;   (plus (??expr (list x p q)) (??expr (list x p q))))

; (define M
;   (synthesize
;     #:forall (list x)
;     #:guarantee (assert (= (interpret sketch) (interpret (mul 10 x))))))

; (evaluate sketch M)

; (define f -16)
; (interpret (shift f 1))

(define-symbolic u integer?)
(define-symbolic i integer?)  ; get access to more constants
(define sketch_new
  (absolute (??expr (list u i))))
  ; (shift u 1))

(define Z
  (synthesize
    #:forall (list u)
    #:guarantee (assert (= (interpret sketch_new) (interpret (iffy (gt u 0) u (neg u)))))))

(evaluate sketch_new Z)
