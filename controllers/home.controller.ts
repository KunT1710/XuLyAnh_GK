import { Request, Response } from "express";

export const home = async ( req: Request, res: Response) =>{
  res.render("pages/home/index",{
    pageTitle: "Trang chủ",

  });
};