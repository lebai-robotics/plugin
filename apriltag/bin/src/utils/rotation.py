import numpy as np
import math

def eulerZyzToRotationMatrix(theta) :
    # 分别构建三个轴对应的旋转矩阵
    R_x = np.array([[1,         0,                  0                   ],
                    [0,         math.cos(theta[2]), -math.sin(theta[2]) ],
                    [0,         math.sin(theta[2]), math.cos(theta[2])  ]
                    ])
    R_y = np.array([[math.cos(theta[1]),    0,      math.sin(theta[1])  ],
                    [0,                     1,      0                   ],
                    [-math.sin(theta[1]),   0,      math.cos(theta[1])  ]
                    ])
    R_z = np.array([[math.cos(theta[0]),    -math.sin(theta[0]),    0],
                    [math.sin(theta[0]),    math.cos(theta[0]),     0],
                    [0,                     0,                      1]
                    ])
    # 将三个矩阵相乘，得到最终的旋转矩阵
    R = np.dot(R_z, np.dot( R_y, R_x ))
    return R

# 检查一个旋转矩阵是否有效
def isRotationMatrix(R) :
    # 得到该矩阵的转置
    Rt = np.transpose(R)
    # 旋转矩阵的一个性质是，相乘后为单位阵
    shouldBeIdentity = np.dot(Rt, R)
    # 构建一个三维单位阵
    I = np.identity(3, dtype = R.dtype)
    # 将单位阵和旋转矩阵相乘后的值做差
    n = np.linalg.norm(I - shouldBeIdentity)
    # 如果小于一个极小值，则表示该矩阵为旋转矩阵
    return n < 1e-6

# 这部分的代码输出与Matlab里边的rotm2euler一致
def rotationMatrixToEulerZyx(R) :
    # 断言判断是否为有效的旋转矩阵
    assert(isRotationMatrix(R))
    sy = math.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
    singular = sy < 1e-6
    if  not singular :
        x = math.atan2(R[2,1] , R[2,2])
        y = math.atan2(-R[2,0], sy)
        z = math.atan2(R[1,0], R[0,0])
    else :
        x = math.atan2(-R[1,2], R[1,1])
        y = math.atan2(-R[2,0], sy)
        z = 0
    return np.array([z, y, x])


if __name__ == "__main__":
    mat = np.array([[9.444320517616471289e-01 ,1.642640750095582525e-01 ,2.847198856183729143e-01],
                    [-2.962673613057895672e-01, 5.017864051458875707e-02, 9.537860109379947549e-01 ],
                    [1.423859200559868809e-01 ,-9.851392884751688506e-01, 9.605640047622143740e-02]
                    ])
    print(rotationMatrixToEulerZyx(mat))