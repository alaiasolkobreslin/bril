#lang rosette

(require rosette/lib/angelic rosette/lib/destruct)

; arithmetic
(struct iffy (condition true false) #:transparent)
(struct plus (left right) #:transparent)
(struct minus (left right) #:transparent)
(struct mul (left right) #:transparent)
(struct div (left right) #:transparent)
(struct square (arg) #:transparent)
(struct neg (arg) #:transparent)
(struct absolute (arg) #:transparent)

; boolean
(struct eq (left right) #:transparent)
(struct lt (left right) #:transparent)
(struct gt (left right) #:transparent)

(define (interpret p)
  (destruct p
    [(iffy a b c)      (if (interpret a) (interpret b) (interpret c))]
    [(plus a b)        (+ (interpret a) (interpret b))]
    [(minus a b)       (- (interpret a) (interpret b))]
    [(mul a b)         (* (interpret a) (interpret b))]
    [(div a b)         (/ (interpret a) (interpret b))]
    [(square a)        (expt (interpret a) 2)]
    [(neg a)           (- (interpret a))]
    [(absolute a)      (abs (interpret a))]

    [(eq a b)          (= (interpret a) (interpret b))]
    [(lt a b)          (< (interpret a) (interpret b))]
    [(gt a b)          (> (interpret a) (interpret b))]
    [_ p]))

(define (??expr terminals)
  (define a (apply choose* terminals))
  (define b (apply choose* terminals))
  (choose*  a
            (neg a)
            (plus a b)
            (minus a b)
            (mul a b)
            (div a b)
            (square a)
            (absolute a)

            (eq a b)
            (lt a b)
            (gt a b)))

(define-symbolic x integer?)
(define-symbolic i j integer?)  ; get access to constants
(define sketch1
  (iffy (??expr (list x i j)) x (??expr (list x i j))))

(define M
  (synthesize
    #:forall (list x)
    #:guarantee (assert (= (interpret sketch1) (interpret (absolute x))))))

(evaluate sketch1 M)



(define-symbolic y integer?)
(define-symbolic a b integer?)  ; get access to constants
(define sketch2
  (mul (??expr (list y a b)) y))

(define N
  (synthesize
    #:forall (list y)
    #:guarantee (assert (= (interpret sketch2) (interpret (square y))))))

(evaluate sketch2 N)


(define-symbolic z integer?)
(define-symbolic c d integer?)  ; get access to constants
(define sketch3
  (absolute (??expr (list z c d))))

(define O
  (synthesize
    #:forall (list z)
    #:guarantee (assert (= (interpret sketch3) (interpret (iffy (gt z 0) z (neg z)))))))

(evaluate sketch3 O)

(define-symbolic e integer?)
(define-symbolic f g integer?)  ; get access to constants
(define sketch4
  (mul (??expr (list e f g)) (??expr (list e f g))))

(define P
  (synthesize
    #:forall (list e)
    #:guarantee (assert (= (interpret sketch4) (mul 2 (mul 2 e))))))

(evaluate sketch4 P)


