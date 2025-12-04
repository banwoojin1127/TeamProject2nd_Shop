-- db 삭제 및 생성
drop database shop;
create database shop;
use shop;

-- 사용자
create table user (
    user_id varchar(255) primary key comment '아이디',
    user_pw varchar(255) not null comment '비밀번호',
    user_name varchar(255) not null comment '이름',
    gender enum('m','f') not null comment '성별',
    birth date comment '생년월일'
) comment '사용자';

-- 카테고리
create table category (
    category_id int auto_increment primary key comment '카테고리 고유 id',
    category_name varchar(100) not null comment '카테고리 이름',
    parent_id int default null comment '상위 카테고리 id (null이면 최상위)',
    foreign key (parent_id) references category (category_id)
) comment '카테고리';

-- 아이템
create table item (
    item_id int auto_increment primary key comment '상품 고유번호',
    item_name varchar(255) not null comment '상품 이름',
    item_price int default 0 comment '상품 가격',
    item_rate float default 0 comment '상품 평점',
    item_reviewcnt int default 0 comment '상품 리뷰수',
    item_img text comment '상품 이미지',
    item_tag varchar(255) comment '상품 태그',
    item_category int comment '상품 카테고리',
    item_feature text comment '상품 특징',
    foreign key(item_category) references category(category_id)
) comment '아이템';

-- 장바구니
create table item_cart (
    cart_id int auto_increment primary key comment '장바구니 고유 id',
    user_id varchar(255) not null comment '사용자 id',
    item_id int not null comment '상품 id',
    foreign key (user_id) references user(user_id),
    foreign key (item_id) references item(item_id)
) comment '사용자 장바구니';

-- 구매 내역
create table purchase_history (
    purchase_id int auto_increment primary key comment '구매 내역 고유 id',
    user_id varchar(255) not null comment '구매한 사용자 id',
    item_id int not null comment '구매한 상품 id',
    foreign key (user_id) references user(user_id),
    foreign key (item_id) references item(item_id)
) comment '사용자 구매 내역';
