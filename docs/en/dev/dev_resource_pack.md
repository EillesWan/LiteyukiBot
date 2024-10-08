---
title: Resource Pack
icon: box
order: 1
category: development
---

## 简介

资源包,亦可根据用途称为主题包、字体包、语言包等，它允许你一定程度上自定义轻雪的外观,并且不用修改源代码

- [资源/主题商店](/store/)提供了一些资源包供你选择，你也可以自己制作资源包
- 资源包的制作很简单，如果你接触过`Minecraft`的资源包，那么你能够很快就上手，仅需按照原有路径进行文件替换即可，讲起打包成一个新的资源包。
- 部分内容制作需要一点点前端基础,例如`html`，`css`
- 轻雪原版资源包请查看`LiteyukiBot/liteyuki/resources`，可以在此基础上进行修改
- 欢迎各位投稿资源包到轻雪资源商店

请注意，主题包中的html渲染使用Js来规定数据的渲染位置，请确保您所编写的html代码能被Bot解析，否则会导致渲染失败或渲染结果不理想/异常/错位等无法预料的事情发生。推荐在编写html时同时更改对应Js代码，以避免出现无法预料的问题。

---

## 加载资源包

- 资源包通常是以`.zip`格式压缩的，只需要将其解压到根目录`resources`目录下即可，注意不要嵌套文件夹,正常的路径应该是这样的

```shell
main.py
resources
└─resource_pack_1
    ├─metadata.yml
    ├─templates
    └───...
└─resource_pack_2
    ├─metadata.yml
    └─...
```

- 你自己制作的资源包也应该遵循这个规则,并且应该在`metadata.yml`中填写一些信息
- 若没有`metadata.yml`文件，则该文件夹不会被识别为资源包

```yaml
name: "资源包名称"
version: "1.0.0"
description: "资源包描述"
# 你可以自定义一些信息,但请保证以上三个字段
...
```

- 资源包加载遵循一个优先级，即后加载的资源包会覆盖前面的资源包，例如，你在A包中定义了一个`index.html`文件，B包也定义了一个`index.html`文件，那么加载B包后，A包中的`index.html`文件会被覆盖
- 对于不同资源包的不同文件，是可以相对引用的，例如你在A中定义了`templates/index.html`，在B中定义了`templates/style.css`，可以在A的`index.html`中用`./style.css`相对路径引用B中的css

> [!tip]
> 资源包的结构会随着轻雪的更新而有变动，第三方资源包开发者需要注意版本兼容性，同时用户也应该自行选择可用的资源包