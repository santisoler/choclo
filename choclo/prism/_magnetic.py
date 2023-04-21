# Copyright (c) 2022 The Choclo Developers.
# Distributed under the terms of the BSD 3-Clause License.
# SPDX-License-Identifier: BSD-3-Clause
#
# This code is part of the Fatiando a Terra project (https://www.fatiando.org)
#
"""
Magnetic forward modelling functions for rectangular prisms
"""
import numpy as np
from numba import jit

from ..constants import VACUUM_MAGNETIC_PERMEABILITY
from ._kernels import kernel_ee, kernel_en, kernel_eu, kernel_nn, kernel_nu, kernel_uu


@jit(nopython=True)
def magnetic_field(easting, northing, upward, prism, magnetization):
    r"""
    Magnetic field due to a rectangular prism

    Returns the three components of the magnetic field due to a single
    rectangular prism on a single computation point.

    .. note::

        Use this function when all the three component of the magnetic fields
        are needed. Running this function is faster than computing each
        component separately. Use one of :func:`magnetic_e`,
        :func:`magnetic_n`, :func:`magnetic_u` if you need only one of them.

    Parameters
    ----------
    easting : float
        Easting coordinate of the observation point. Must be in meters.
    northing : float
        Northing coordinate of the observation point. Must be in meters.
    upward : float
        Upward coordinate of the observation point. Must be in meters.
    prism : 1d-array
        One dimensional array containing the coordinates of the prism in the
        following order: ``west``, ``east``, ``south``, ``north``, ``bottom``,
        ``top`` in a Cartesian coordinate system.
        All coordinates should be in meters.
    magnetization : 1d-array
        Magnetization vector of the prism. It should have three components in
        the following order: ``magnetization_easting``,
        ``magnetization_northing``, ``magnetization_upward``.
        Should be in :math:`A m^{-1}`.

    Returns
    -------
    b_e, b_n, b_u : floats
        The three components of the magnetic field generated by the prism on
        the observation point in :math:`\text{T}`.
        The components are returned in the following order: ``b_e``, ``b_n``,
        ``b_u``.

    Notes
    -----
    Consider an observation point :math:`\mathbf{p}` and a prism :math:`R` with
    a magnetization vector :math:`\mathbf{M}`. The magnetic field
    :math:`\mathbf{B}` it generates on the observation point :math:`\mathbf{p}`
    is defined as:

    .. math::

        \mathbf{B}(\mathbf{p}) =
            - \frac{\mu_0}{4\pi} \nabla_\mathbf{p}
            \left[
            \int\limits_R \mathbf{M} \cdot \nabla_\mathbf{q}
            \left( \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert} \right)
            dv
            \right]

    Since the magnetization vector is constant inside the boundaries of the
    prism, we can write the easting component of :math:`\mathbf{B}` as:

    .. math::

        B_x(\mathbf{p}) =
            - \frac{\mu_0}{4\pi}
            \left[
                M_x \int\limits_R
                \frac{\partial}{\partial x_p}
                \left[
                \frac{\partial}{\partial x_q}
                \left( \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert} \right)
                \right]
                dv
                +
                M_y \int\limits_R
                \frac{\partial}{\partial x_p}
                \left[
                \frac{\partial}{\partial y_q}
                \left( \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert} \right)
                \right]
                dv
                +
                M_z \int\limits_R
                \frac{\partial}{\partial x_p}
                \left[
                \frac{\partial}{\partial z_q}
                \left( \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert} \right)
                \right]
                dv
            \right]

    where :math:`M_x`, :math:`M_y` and :math:`M_z` are the components of the
    magnetization vector. The other components can be expressed in an analogous
    way.

    It can be proved that

    .. math::

        \frac{\partial}{\partial x_q}
        \left( \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert} \right)
        =
        - \frac{\partial}{\partial x_p}
        \left( \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert} \right)

    and that it also holds for the two other directions. Therefore, we can
    rewrite :math:`B_x` as:

    .. math::

        B_x(\mathbf{p}) =
            + \frac{\mu_0}{4\pi}
            \left[
                M_x
                \frac{\partial^2}{\partial x_p^2}
                \int\limits_R
                \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert}
                dv
                +
                M_y
                \frac{\partial^2}{\partial x_p \partial y_p}
                \int\limits_R
                \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert}
                dv
                +
                M_z
                \frac{\partial^2}{\partial x_p \partial z_p}
                \int\limits_R
                \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert}
                dv
            \right]

    Solutions to each one of the integrals in the previous equation and their
    second derivatives are given by [Nagy2000]_.

    Following [Oliveira2015]_ we can define a symmetrical 3x3 matrix
    :math:`\mathbf{U}` whose elements are the second derivatives of the
    previous integrals, such as:

    .. math::

        u_{ij} =
            \frac{\partial}{\partial i}
            \frac{\partial}{\partial j}
            \int\limits_R
            \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert}
            dv

    with :math:`i, j \in \{x, y, z\}`.

    We can then express the magnetic field :math:`\mathbf{B}(\mathbf{p})`
    generated by the prism in a compact form:

    .. math::

        \mathbf{B}(\mathbf{p}) = \frac{\mu_0}{4\pi} \mathbf{U} \cdot \mathbf{M}


    References
    ----------
    - [Blakely1995]_
    - [Oliveira2015]_
    - [Nagy2000]_
    - [Nagy2002]_
    - [Fukushima2020]_

    See also
    --------
    :func:`choclo.prism.magnetic_e`
    :func:`choclo.prism.magnetic_n`
    :func:`choclo.prism.magnetic_u`
    """
    # Initialize magnetic field vector components
    b_e, b_n, b_u = 0.0, 0.0, 0.0
    # Iterate over the vertices of the prism
    for i in range(2):
        # Compute shifted easting coordinate
        shift_east = prism[1 - i] - easting
        shift_east_sq = shift_east**2
        for j in range(2):
            # Compute shifted northing coordinate
            shift_north = prism[3 - j] - northing
            shift_north_sq = shift_north**2
            for k in range(2):
                # Compute shifted upward coordinate
                shift_upward = prism[5 - k] - upward
                shift_upward_sq = shift_upward**2
                # Compute the radius
                radius = np.sqrt(shift_east_sq + shift_north_sq + shift_upward_sq)
                # Compute all kernel tensor components for the current vertex
                k_ee = kernel_ee(shift_east, shift_north, shift_upward, radius)
                k_nn = kernel_nn(shift_east, shift_north, shift_upward, radius)
                k_uu = kernel_uu(shift_east, shift_north, shift_upward, radius)
                k_en = kernel_en(shift_east, shift_north, shift_upward, radius)
                k_eu = kernel_eu(shift_east, shift_north, shift_upward, radius)
                k_nu = kernel_nu(shift_east, shift_north, shift_upward, radius)
                # Get the sign of this terms based on the current vertex
                sign = (-1) ** (i + j + k)
                # Compute the dot product between the kernel tensor and the
                # magnetization vector of the prism
                b_e += sign * (
                    magnetization[0] * k_ee
                    + magnetization[1] * k_en
                    + magnetization[2] * k_eu
                )
                b_n += sign * (
                    magnetization[0] * k_en
                    + magnetization[1] * k_nn
                    + magnetization[2] * k_nu
                )
                b_u += sign * (
                    magnetization[0] * k_eu
                    + magnetization[1] * k_nu
                    + magnetization[2] * k_uu
                )
    c_m = VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi
    b_e *= c_m
    b_n *= c_m
    b_u *= c_m
    return b_e, b_n, b_u


@jit(nopython=True)
def magnetic_e(easting, northing, upward, prism, magnetization):
    r"""
    Easting component of the magnetic field due to a prism

    Returns the easting component of the magnetic field due to a single
    rectangular prism on a single computation point.

    Parameters
    ----------
    easting : float
        Easting coordinate of the observation point. Must be in meters.
    northing : float
        Northing coordinate of the observation point. Must be in meters.
    upward : float
        Upward coordinate of the observation point. Must be in meters.
    prism : 1d-array
        One dimensional array containing the coordinates of the prism in the
        following order: ``west``, ``east``, ``south``, ``north``, ``bottom``,
        ``top`` in a Cartesian coordinate system.
        All coordinates should be in meters.
    magnetization : 1d-array
        Magnetization vector of the prism. It should have three components in
        the following order: ``magnetization_easting``,
        ``magnetization_northing``, ``magnetization_upward``.
        Should be in :math:`A m^{-1}`.

    Returns
    -------
    b_e : float
        Easting component of the magnetic field generated by the prism
        on the observation point in :math:`\text{T}`.

    Notes
    -----
    Computes the easting component of the magnetic field
    :math:`\mathbf{B}(\mathbf{p})` generated by a rectangular prism :math:`R`
    with a magnetization vector :math:`M` on the observation point
    :math:`\mathbf{p}` as follows:

    .. math::

        B_x(\mathbf{p}) =
            \frac{\mu_0}{4\pi}
            \left( M_x u_{xx} + M_y u_{xy} + M_z u_{xz} \right)

    Where :math:`u_{ij}` are:

    .. math::

        u_{ij} =
            \frac{\partial}{\partial i}
            \frac{\partial}{\partial j}
            \int\limits_R
            \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert}
            dv

    with :math:`i,j \in \{x, y, z\}`.
    Solutions of the second derivatives of these integrals are given by
    [Nagy2000]_:

    .. math::

        u_{xx} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            - \arctan \left( \frac{yz}{xr} \right)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}
        \\
        u_{xy} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            \ln (z + r)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}
        \\
        u_{xz} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            \ln (y + r)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}

    References
    ----------
    - [Blakely1995]_
    - [Oliveira2015]_
    - [Nagy2000]_
    - [Nagy2002]_
    - [Fukushima2020]_

    See also
    --------
    :func:`choclo.prism.magnetic_field`
    :func:`choclo.prism.magnetic_n`
    :func:`choclo.prism.magnetic_u`
    """
    # Initialize magnetic field vector component
    b_e = 0.0
    # Iterate over the vertices of the prism
    for i in range(2):
        # Compute shifted easting coordinate
        shift_east = prism[1 - i] - easting
        shift_east_sq = shift_east**2
        for j in range(2):
            # Compute shifted northing coordinate
            shift_north = prism[3 - j] - northing
            shift_north_sq = shift_north**2
            for k in range(2):
                # Compute shifted upward coordinate
                shift_upward = prism[5 - k] - upward
                shift_upward_sq = shift_upward**2
                # Compute the radius
                radius = np.sqrt(shift_east_sq + shift_north_sq + shift_upward_sq)
                # Compute kernel tensor components for the current vertex
                k_ee = kernel_ee(shift_east, shift_north, shift_upward, radius)
                k_en = kernel_en(shift_east, shift_north, shift_upward, radius)
                k_eu = kernel_eu(shift_east, shift_north, shift_upward, radius)
                # Compute b_e using the dot product between the kernel tensor
                # and the magnetization vector of the prism
                b_e += (-1) ** (i + j + k) * (
                    magnetization[0] * k_ee
                    + magnetization[1] * k_en
                    + magnetization[2] * k_eu
                )
    return VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi * b_e


@jit(nopython=True)
def magnetic_n(easting, northing, upward, prism, magnetization):
    r"""
    Northing component of the magnetic field due to a prism

    Returns the northing component of the magnetic field due to a single
    rectangular prism on a single computation point.

    Parameters
    ----------
    easting : float
        Easting coordinate of the observation point. Must be in meters.
    northing : float
        Northing coordinate of the observation point. Must be in meters.
    upward : float
        Upward coordinate of the observation point. Must be in meters.
    prism : 1d-array
        One dimensional array containing the coordinates of the prism in the
        following order: ``west``, ``east``, ``south``, ``north``, ``bottom``,
        ``top`` in a Cartesian coordinate system.
        All coordinates should be in meters.
    magnetization : 1d-array
        Magnetization vector of the prism. It should have three components in
        the following order: ``magnetization_easting``,
        ``magnetization_northing``, ``magnetization_upward``.
        Should be in :math:`A m^{-1}`.

    Returns
    -------
    b_n : float
        Northing component of the magnetic field generated by the prism
        on the observation point in :math:`\text{T}`.

    Notes
    -----
    Computes the northing component of the magnetic field
    :math:`\mathbf{B}(\mathbf{p})` generated by a rectangular prism :math:`R`
    with a magnetization vector :math:`M` on the observation point
    :math:`\mathbf{p}` as follows:

    .. math::

        B_y(\mathbf{p}) =
            \frac{\mu_0}{4\pi}
            \left( M_x u_{xy} + M_y u_{yy} + M_z u_{yz} \right)

    Where :math:`u_{ij}` are:

    .. math::

        u_{ij} =
            \frac{\partial}{\partial i}
            \frac{\partial}{\partial j}
            \int\limits_R
            \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert}
            dv

    with :math:`i,j \in \{x, y, z\}`.
    Solutions of the second derivatives of these integrals are given by
    [Nagy2000]_:

    .. math::

        u_{xy} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            \ln (z + r)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}
        \\
        u_{yy} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            - \arctan \left( \frac{xz}{yr} \right)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}
        \\
        u_{yz} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            \ln (x + r)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}

    References
    ----------
    - [Blakely1995]_
    - [Oliveira2015]_
    - [Nagy2000]_
    - [Nagy2002]_
    - [Fukushima2020]_

    See also
    --------
    :func:`choclo.prism.magnetic_field`
    :func:`choclo.prism.magnetic_e`
    :func:`choclo.prism.magnetic_u`
    """
    # Initialize magnetic field vector component
    b_n = 0.0
    # Iterate over the vertices of the prism
    for i in range(2):
        # Compute shifted easting coordinate
        shift_east = prism[1 - i] - easting
        shift_east_sq = shift_east**2
        for j in range(2):
            # Compute shifted northing coordinate
            shift_north = prism[3 - j] - northing
            shift_north_sq = shift_north**2
            for k in range(2):
                # Compute shifted upward coordinate
                shift_upward = prism[5 - k] - upward
                shift_upward_sq = shift_upward**2
                # Compute the radius
                radius = np.sqrt(shift_east_sq + shift_north_sq + shift_upward_sq)
                # Compute kernel tensor components for the current vertex
                k_nn = kernel_nn(shift_east, shift_north, shift_upward, radius)
                k_en = kernel_en(shift_east, shift_north, shift_upward, radius)
                k_nu = kernel_nu(shift_east, shift_north, shift_upward, radius)
                # Compute b_n using the dot product between the kernel tensor
                # and the magnetization vector of the prism
                b_n += (-1) ** (i + j + k) * (
                    magnetization[0] * k_en
                    + magnetization[1] * k_nn
                    + magnetization[2] * k_nu
                )
    return VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi * b_n


@jit(nopython=True)
def magnetic_u(easting, northing, upward, prism, magnetization):
    r"""
    Upward component of the magnetic field due to a prism

    Returns the upward component of the magnetic field due to a single
    rectangular prism on a single computation point.

    Parameters
    ----------
    easting : float
        Easting coordinate of the observation point. Must be in meters.
    northing : float
        Northing coordinate of the observation point. Must be in meters.
    upward : float
        Upward coordinate of the observation point. Must be in meters.
    prism : 1d-array
        One dimensional array containing the coordinates of the prism in the
        following order: ``west``, ``east``, ``south``, ``north``, ``bottom``,
        ``top`` in a Cartesian coordinate system.
        All coordinates should be in meters.
    magnetization : 1d-array
        Magnetization vector of the prism. It should have three components in
        the following order: ``magnetization_easting``,
        ``magnetization_northing``, ``magnetization_upward``.
        Should be in :math:`A m^{-1}`.

    Returns
    -------
    b_u : float
        Upward component of the magnetic field generated by the prism
        on the observation point in :math:`\text{T}`.

    Notes
    -----
    Computes the upward component of the magnetic field
    :math:`\mathbf{B}(\mathbf{p})` generated by a rectangular prism :math:`R`
    with a magnetization vector :math:`M` on the observation point
    :math:`\mathbf{p}` as follows:

    .. math::

        B_z(\mathbf{p}) =
            \frac{\mu_0}{4\pi}
            \left( M_x u_{xz} + M_y u_{yz} + M_z u_{zz} \right)

    Where :math:`u_{ij}` are:

    .. math::

        u_{ij} =
            \frac{\partial}{\partial i}
            \frac{\partial}{\partial j}
            \int\limits_R
            \frac{1}{\lVert \mathbf{p} - \mathbf{q} \rVert}
            dv

    with :math:`i,j \in \{x, y, z\}`.
    Solutions of the second derivatives of these integrals are given by
    [Nagy2000]_:

    .. math::

        u_{xz} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            \ln (y + r)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}
        \\
        u_{yz} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            \ln (x + r)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}
        \\
        u_{zz} &=
            \Bigg\lvert\Bigg\lvert\Bigg\lvert
            - \arctan \left( \frac{xy}{zr} \right)
            \Bigg\rvert_{X_1}^{X_2}
            \Bigg\rvert_{Y_1}^{Y_2}
            \Bigg\rvert_{Z_1}^{Z_2}

    References
    ----------
    - [Blakely1995]_
    - [Oliveira2015]_
    - [Nagy2000]_
    - [Nagy2002]_
    - [Fukushima2020]_

    See also
    --------
    :func:`choclo.prism.magnetic_field`
    :func:`choclo.prism.magnetic_e`
    :func:`choclo.prism.magnetic_n`
    """
    # Initialize magnetic field vector component
    b_u = 0.0
    # Iterate over the vertices of the prism
    for i in range(2):
        # Compute shifted easting coordinate
        shift_east = prism[1 - i] - easting
        shift_east_sq = shift_east**2
        for j in range(2):
            # Compute shifted northing coordinate
            shift_north = prism[3 - j] - northing
            shift_north_sq = shift_north**2
            for k in range(2):
                # Compute shifted upward coordinate
                shift_upward = prism[5 - k] - upward
                shift_upward_sq = shift_upward**2
                # Compute the radius
                radius = np.sqrt(shift_east_sq + shift_north_sq + shift_upward_sq)
                # Compute kernel tensor components for the current vertex
                k_uu = kernel_uu(shift_east, shift_north, shift_upward, radius)
                k_eu = kernel_eu(shift_east, shift_north, shift_upward, radius)
                k_nu = kernel_nu(shift_east, shift_north, shift_upward, radius)
                # Compute b_n using the dot product between the kernel tensor
                # and the magnetization vector of the prism
                b_u += (-1) ** (i + j + k) * (
                    magnetization[0] * k_eu
                    + magnetization[1] * k_nu
                    + magnetization[2] * k_uu
                )
    return VACUUM_MAGNETIC_PERMEABILITY / 4 / np.pi * b_u