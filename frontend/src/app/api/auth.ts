import axios from "axios";

const API_URL = "/api";
export type RegisterData = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role?: string;
};

export type RegisterResponse = {
  message: string;
};

export async function registerUser(
  data: RegisterData
): Promise<RegisterResponse> {

  const response = await axios.post(
    `${API_URL}/auth/register`,
    data
  );

  return response.data;
}
export interface signinData {
  email: string;
  password: string;
}

export async function signinUser(data: signinData) {

  const response = await axios.post(
    `${API_URL}/auth/signin`,
    data
  );

  return response.data;
}

export async function forgotPassword(email: string) {
  const response = await axios.post(
    `${API_URL}/auth/forgot-password`,
    {
      email,
    }
  );

  return response.data;
}

export async function resetPassword(
  token: string,
  newPassword: string
) {
  const response = await axios.post(
    `${API_URL}/auth/reset-password`,
    {
      token,
      new_password: newPassword,
    }
  );

  return response.data;
}