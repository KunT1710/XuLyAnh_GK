import { Request, Response } from "express";

export const edit = async ( req: Request, res: Response) =>{

  res.render("pages/edit/edit",{
    pageTitle: "Chỉnh sửa hình ảnh ",
  });
  
};